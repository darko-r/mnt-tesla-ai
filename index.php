<?php
session_start();

// Import functions
require_once('../includes/initialize.php');
require_once('./dotenv.php');

if ( empty($_SESSION['csrf_token']) ) {
    $_SESSION['csrf_token'] = bin2hex(openssl_random_pseudo_bytes(32));
}

if ( isset($_POST['action']) && isset($_POST['question']) ) {

    // Verify CSRF token
    if ( isset($_POST['csrf_token']) && $_POST['csrf_token'] === $_SESSION['csrf_token'] ) {

        if ( $_POST['action'] === 'prompt' ) {
            (new DotEnv('./.env'))->load();
            prompt($_POST['question']);
        }

    } else {
        header('Cache-Control: no-cache, must-revalidate');
        header('Content-type: application/json');
        echo json_encode( array('error' => 'Invalid CSRF token') );
        exit();
    }

}


function prompt($question) {

    try {
        $embeddings = getEmbeddings($question);
        $ids = getSimilarityIDs($embeddings);
        $data = getPagesFromDatabase($ids);
        $answer = getAnswerFromOpenai($question, $data['context']);

        $response = array(
            "answer" => $answer,
            "source" => $data['source']
        );
    } catch (Exception $exception) {
        $response = array( 
            "error" => $exception->getMessage() 
        );
    }

    header('Cache-Control: no-cache, must-revalidate');
    header('Content-type: application/json');
    echo json_encode($response);
    exit();
}

function getEmbeddings($text) {
    $openaiApiKey = getenv('OPENAI_API_KEY');

	// Set the request headers
	$headers = array(
		"Authorization: Bearer $openaiApiKey",
		"Content-Type: application/json"
	);

	// Prepare the request data
	$data = array(
		"input" => $text,
		"model" => "text-embedding-ada-002"
	);

    $curl = curl_init();
    curl_setopt($curl, CURLOPT_URL, "https://api.openai.com/v1/embeddings");
    curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($curl, CURLOPT_HTTPHEADER, $headers);
    curl_setopt($curl, CURLOPT_POST, true);
    curl_setopt($curl, CURLOPT_POSTFIELDS, json_encode($data));

    $response = curl_exec($curl);

    if ($response !== false) {
        $responseData = json_decode($response);

        curl_close($curl);
        return $responseData->data[0]->embedding;
    } else {
        curl_close($curl);
        throw new Exception("Failed to generate embeddings");
    }
}

function getSimilarityIDs($embeddings) {
    $pineconeApiKey = getenv('PINECONE_API_KEY');

    $data = array(
        "topK" => 2,
		"vector" => $embeddings,
		"namespace" => "pages",
        "includeValues" => false,
        "includeMetadata" => false
	);
    
    $curl = curl_init();

    curl_setopt_array($curl, [
        CURLOPT_URL => "https://pages-353c6e1.svc.asia-southeast1-gcp-free.pinecone.io/query",
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_ENCODING => "",
        CURLOPT_MAXREDIRS => 10,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
        CURLOPT_CUSTOMREQUEST => "POST",
        CURLOPT_POSTFIELDS => json_encode($data),
        CURLOPT_HTTPHEADER => [
            "Api-Key: $pineconeApiKey",
            "accept: application/json",
            "content-type: application/json"
        ]
    ]);

    $response = curl_exec($curl);

    if ($response !== false) {
        $ids = [];
        $decoded_response = json_decode($response);

        foreach ($decoded_response->matches as $match) {
            array_push($ids, $match->id);
        }

        curl_close($curl);
        return $ids;
    } else {
        curl_close($curl);
        throw new Exception("Failed to get similarity IDs");
    }
}

function getPagesFromDatabase($ids) {
    $query = "
        SELECT document_id, documentpages.id, documents.title, documents.date, documents.type, documentpages.page_number, content
		FROM documentpages INNER JOIN documents ON documents.id = documentpages.document_id
		WHERE documentpages.id IN (" . implode(",", $ids) . ");
    ";

    // Connect to database
    include '../includes/database-connection.php';

    $rows = $connection->query($query);

    if (!$rows || $rows->num_rows < 1) {
        throw new Exception("Failed to fetch pages from database: " . $connection->error);
    }

    $results = [];
    while( $row = $rows->fetch_assoc() ) {
        $results[] = $row;
    }

    $source = [];
    $context = "";
    $page_separator = ". ";

    foreach ($results as $result) {
        array_push($source, array(
            "title" => $result['title'],
            "date" => $result['date'],
            "page" => $result['page_number'],
            "link" => "../preview/?id=" . $result['document_id'] . "&p=" . $result['page_number']
        ));

        $context .= $result['content'] . $page_separator;
    }


    return array( 
        "source" => $source, 
        "context" => rtrim($context, $page_separator) 
    );
}

function getAnswerFromOpenai($question, $context) {
    $openaiApiKey = getenv('OPENAI_API_KEY');

    $pre_prompt = "Pretend you are Nikola Tesla and answer questions as you are him.
        If the answer is available in the context provided, answer based on that context. 
        If the question is not covered in the context and you are confident in your knowledge, answer the question by yourself.
    ";

    $headers = array(
		"Authorization: Bearer $openaiApiKey",
		"Content-Type: application/json"
	);

	$prompt_text = $pre_prompt . " Context: " . $context . " Question: " . $question . "? ";
	$prompt_text = str_replace(["\n","\r", "\t"], "", $prompt_text);
	$prompt_text = ltrim($prompt_text);

    $data = array(
		//"model" => "text-curie-001",
		"model" => "text-davinci-003",
        "prompt" => "$prompt_text",
        "temperature" => floatval(0.6),
        "max_tokens" => intval(400),
        "top_p" => 1,
        "frequency_penalty" => 0,
        "presence_penalty" => 0
	);

    $curl = curl_init();
    curl_setopt($curl, CURLOPT_URL, "https://api.openai.com/v1/completions");
    curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($curl, CURLOPT_HTTPHEADER, $headers);
    curl_setopt($curl, CURLOPT_POST, true);
    curl_setopt($curl, CURLOPT_POSTFIELDS, json_encode($data));

    $response = curl_exec($curl);

    if ($response !== false) {
        $responseData = json_decode($response);

        curl_close($curl);
        return trim($responseData->choices[0]->text);
    } else {
        curl_close($curl);
        throw new Exception("Failed to generate answer");
    }
}


include 'page.php';
?>