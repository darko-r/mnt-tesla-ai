<?php
require_once('./embedding-sample.php');
require_once('../dotenv.php');

$document = new DOMDocument();
$file = './log.html';

date_default_timezone_set('Europe/Belgrade');

function getSimilarityIDs($embeddings) {
    (new DotEnv('../.env'))->load();
    $pineconeApiKey = getenv('PINECONE_API_KEY');

    $data = array(
        "topK" => 2,
		"vector" => $embeddings->vector,
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

$ids = getSimilarityIDs( $embeddings_sample );

if( $document->loadHTMLFile($file) ) {
    $document->getElementById('cron-date')->nodeValue = date('d-m-Y H:i:s');
    $document->getElementById('return-id')->nodeValue = "{$ids[0]}-{$ids[1]}";
    $document->saveHTMLFile($file);
}