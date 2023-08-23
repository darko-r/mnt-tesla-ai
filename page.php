<!DOCTYPE html>

<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0" />
        <link rel="icon" href="<?php echo url_for('media/images/favicon.svg') ?>">
        <link rel="mask-icon" href="<?php echo url_for('media/images/favicon.svg') ?>" color="#396271">


        <title>Nikola Tesla Database | AI</title>


        <link rel="stylesheet" href="../css/reset.css">
        <link rel="stylesheet" href="../css/fonts.css">

        <link href="../css/base.css" rel="stylesheet">
        <link href="../css/pages-template.css" rel="stylesheet">

        <!-- JQuery -->
        <script src="https://code.jquery.com/jquery-3.1.0.min.js" integrity="sha256-cCueBR6CsyA4/9szpPfrX3s49M9vUU5BgtiJj06wt/s=" crossorigin="anonymous"></script>

        <script src="../js/header.js"></script>

        <script>
            window.addEventListener('load', () => {
                const csrfToken = document.getElementById('csrf_token').value;
                const promptInput = document.getElementById('js-prompt-text');
                const promptSubmit = document.getElementById('js-prompt-submit');
                const promptForm = document.querySelector('.prompt-form');
                const chatContainer = document.querySelector('.chat-container');
                const starterHowTo = document.getElementById('starter-how-to');

                async function submitPrompt() {
                    if (!promptForm.classList.contains('can-submit')) {
                        return;
                    }

                    starterHowTo.classList.add('hide');

                    const question = promptInput.textContent.trim();
                    promptInput.textContent = '';
                    promptForm.classList.replace('can-submit', 'busy');
                    chatContainer.appendChild(createMessage(question));
                    const answer = createMessage();
                    answer.classList.add('bot', 'waiting');
                    chatContainer.appendChild(answer);
                    window.scrollTo(0, document.body.scrollHeight);

                    const response = await makePrompt(question);
                    console.table(response);
                    answer.classList.remove('waiting');

                    if (!response.error) {
                        const isAnswered = !['', ' ', 'unanswerable', 'unanswerable.', "'unanswerable'", "'unanswerable'."].includes(response.answer.toLowerCase());

                        if (!isAnswered) {
                            response.answer = 'I am unable to give a suitable response based on the information provided. By including more specific information, I\'ll be able to offer a more accurate and helpful answer. Please provide further context and rephrase your question.';
                        }

                        displayAnswerText(response.answer, answer.querySelector('p'), () => {
                            promptForm.classList.remove('busy');
                            if (isAnswered) {
                                const source = createSource(response.source);
                                answer.appendChild(source);
                                setTimeout(() => answer.classList.add('has-source'), 200);
                            }
                        });
                    } else {
                        promptForm.classList.remove('busy');
                        console.error(`NikolaTeslaDatabase: ${response.error}`);
                    }
                }

                async function displayAnswerText(text, element, callback) {
                    let index = 0;
                    let words = text.split(' ');

                    (function typeWords() {
                        if (index < words.length) {
                            element.textContent += ` ${words[index]}`;
                            window.scrollTo(0, document.body.scrollHeight);
                            index += 1;
                            setTimeout(typeWords, 50);
                        } else {
                            if (callback) {
                                callback();                                
                            }
                        }
                    }());
                }


                function createMessage(content = '') {
                    const container = document.createElement('div');
                    container.classList.add('message-container');
                    const article = document.createElement('article');
                    article.classList.add('message');
                    const text = document.createElement('p');
                    text.textContent = content;
                    article.appendChild(text);
                    container.appendChild(article);
                    return container;
                }

                function createSource(sources) {
                    const source = document.createElement('article');
                    source.classList.add('source');
                    const button = document.createElement('button');
                    button.setAttribute('title', 'View the answer source');
                    button.addEventListener( 'click', event => event.target.parentElement.classList.toggle('expanded') );
                    source.appendChild(button);
                    const links = document.createElement('div');
                    links.classList.add('links');
                    source.appendChild(links);

                    sources.forEach( source => {
                        const link = document.createElement('a');
                        link.setAttribute('target', '_blank');
                        link.setAttribute('href', source.link);
                        link.textContent = `${source.title} (${source.date}), page ${source.page}`;
                        links.appendChild(link);
                    });

                    return source;
                }

                async function makePrompt(question) {
                    const requestData = new FormData();
                    requestData.append('action', 'prompt');
                    requestData.append('question', question);
                    requestData.append('csrf_token', encodeURIComponent(csrfToken));

                    const requestInit = {
                        method: 'POST',
                        body: requestData
                    }

                    const response = await fetch('', requestInit);
                    return await response.json();
                }

                // Disable form submition.
                promptForm.addEventListener('submit', event => {
                    event.preventDefault();
                }, true);

                promptSubmit.addEventListener('click', submitPrompt);
                promptInput.addEventListener('keydown', event => {
                    if ((event.code === 'Enter' || event.code === 'NumpadEnter') && !event.shiftKey) {
                        event.preventDefault();
                        submitPrompt();
                    }
                });

                promptInput.addEventListener('input', event => {
                    if (event.target.textContent.trim().length) {
                        promptForm.classList.add('can-submit');
                    } else {
                        promptForm.classList.remove('can-submit');
                    }
                });
            });
        </script>
        <style>
            html {
                scroll-behavior: smooth;
            }

            .chat-container {
                display: flex;
                flex-direction: column;
                background-color: #fff;
                font-family: 'Usual Light';
            }

            .prompt-form {
                position: fixed;
                left: 50%;
                bottom: 0;
                width: 100%;
                max-width: 1500px;
                padding: 4rem 40px 0 40px;
                background-image: linear-gradient(180deg, rgba(255, 255, 255, 0), #ffffff 58.85%);
                box-sizing: border-box;
                transform: translateX(-50%);
                z-index: 100;
            }

            @media screen and (max-width: 768px) {
                .prompt-form {
                    padding: 4rem 20px 0 20px;
                }
            }

            #js-prompt-text {
                display: block;
                width: 100%;
                min-height: 24px;
                max-height: 120px;
                resize: none;
                line-height: 24px;
                font-size: 1rem;
                padding: 0px;
                margin: 0;
                border: 0px none;
                outline: none;
                color: #fff;
                background-color: transparent;
                font-family: inherit;
                overflow-y: auto;
                font-family: 'Usual Regular';
            }

            .busy #js-prompt-text {
                pointer-events: none;
            }

            .busy #js-prompt-text:empty::before {
                opacity: 0.2;
            }

            #js-prompt-text:empty::before {
                content: "Ask a question.";
                cursor: text;
                color: #fff;
                opacity: .8;
                transition: opacity 200ms ease-in-out;
            }

            #js-prompt-submit {
                position: absolute;
                right: 0;
                bottom: 0.75rem;
                width: 32px;
                height: 32px;
                padding: 6px;
                margin-right: 1rem;
                border: none;
                border-radius: 8px;
                color: #ffffff66;
                background-color: transparent;
                transition: opacity 200ms ease-in-out;
            }

            .busy #js-prompt-submit {
                opacity: 0.2;
            }

            #js-prompt-submit,
            #js-prompt-submit > svg {
                transition: background-color .25s ease-in-out, color .25s ease-in-out;
            }

            .can-submit #js-prompt-submit {
                cursor: pointer;
                color: #9b7e51;
                background-color: #ffc569;
            }

            .prompt-form fieldset {
                max-width: 48rem;
                margin: auto;
                display: flex;
                padding: 1rem;
                position: relative;
                background-color: #325561;
                border-radius: 8px;
                box-sizing: border-box;
                transition: opacity 200ms ease-in-out;
            }

            .busy .prompt-form fieldset {
                opacity: 0.8;
            }

            .prompt-form fieldset > div {
                width: 100%;
                margin-right: 3rem;
            }

            .prompt-form small {
                display: block;
                margin: 0 auto;
                color: #888;
                opacity: 0.8;
                font-size: 12px;
                margin: 0.6rem auto 0.8rem auto;
                text-align: center;
            }

            .chat-container .message-container {
                padding: 1.5rem 40px;
                border-bottom: 1px solid rgba(0, 0, 0, 0.1);
            }

            @media screen and (max-width: 768px) {
                .chat-container .message-container {
                    padding: 1.5rem 20px;
                }
            }

            .chat-container .message-container.bot {
                background-color: #f7f7f7;
            }

            .chat-container .message-container.bot.has-source {
                padding-bottom: 0.5rem;
            }

            .chat-container .message {
                max-width: 48rem;
                margin: 0 auto;
            }

            .message > p {
                display: flex;
                padding-right: calc(30px + 1.5rem);
            }

            .message > p::before {
                content: ' ';
                flex-shrink: 0;
                position: relative;
                top: -3px;
                display: inline-block;
                width: 30px;
                height: 30px;
                margin-right: 1.5rem;
                border-radius: 3px;
                background-color: #cecece;
                background-position: center;
                background-repeat: no-repeat;
                background-size: 75%;
            }
            
            .bot .message > p::before {
                background-color: #738e95;
                background-image: url('../media/images/logo.svg');
            }

            .waiting .message > p::after {
                content: ' ';
                display: block;
                width: 8px;
                height: 20px;
                background-color: black;
                position: relative;
                top: 2px;
                margin-left: 2px;
                animation: 1s ease-in-out infinite on-off;
            }

            .chat-container .source {
                display: none;
                flex-direction: column;
                align-items: flex-end;
                max-width: 48rem;
                padding-top: 1rem;
                margin: 0 auto;
                overflow: hidden;
            }

            .chat-container .has-source .source {
                display: flex;
            }

            .chat-container .source > button {
                display: block;
                padding: 0;
                border: none;
                background-color: transparent;
                color: #a0a0a0;
                transition: filter 200ms ease-in-out, opacity 200ms ease-in-out;
                cursor: pointer;
                width: 1rem;
                height: 1rem;
                background-image: url('../media/images/question-mark-in-square.svg');
                background-position: center;
                background-repeat: no-repeat;
                background-size: 100%;
            }

            .chat-container .source > button:hover {
                filter: brightness(0.2) sepia(1) hue-rotate(180deg) saturate(5);
                opacity: 0.9;
            }

            .chat-container .source > .links {
                align-self: stretch;
                position: relative;
                top: 1px;
                display: flex;
                flex-direction: column;
                align-items: flex-start;
                margin: 0 calc(30px + 1.5rem);
                gap: 0.2rem;
                max-height: 0;
                border-top: 1px solid #cacaca;
                font-size: 0.9rem;
                transition: max-height 250ms ease-in-out;
            }

            .chat-container .source.expanded > .links {
                max-height: 200px;
                transition: max-height 500ms ease-in-out;
            }

            .chat-container .source > .links > a {
                color: #777;
                transition: color 200ms ease-in-out;
            }

            .chat-container .source > .links > a:first-child {
                margin: 0.25rem 0;
            }

            .chat-container .source > .links > a:last-child {
                margin-bottom: 0.5rem;
            }

            .chat-container .source > .links > a:hover {
                color: #555;
            }

            .chat-container #spacer {
                order: 2;
                width: 100%;
                height: 12rem;
                margin-top: auto;
            }

            .dot-animation {
                position: relative;
                display: flex;
                margin: 0 auto;
                width: 72px;
                margin-bottom: 20px;
                opacity: 0;
                transition: opacity 200ms ease-in-out;
            }

            .busy .dot-animation {
                opacity: 1;
            }

            .dot{
                content: ' ';
                position: relative;
                display: block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: black;
                margin: 0 4px;
                background: #ffc15e;
            }

            .dot.first {
                animation: 1.5s ease-in-out 200ms infinite bounce;
            }

            .dot.second {
                animation: 1.5s ease-in-out 500ms infinite bounce;
            }

            .dot.third {
                animation: 1.5s ease-in-out 800ms infinite bounce;
            }

            @keyframes bounce {
                0%, 15% { transform: translateY(0); }
                50% { transform: translateY(-12px); }
                85%, 100% { transform: translateY(0); }
            }

            @keyframes on-off {
                0%   { opacity: 0; }
                100% { opacity: 1; }
            }

            #starter-how-to {
                align-self: center;
                position: relative;
                top: 15%;
                display: grid;
                max-width: 48rem;
                margin: 0 40px;
                grid-template-columns: 1fr 1fr 1fr;
                color: #17303b;
                grid-column-gap: .8rem;
                font-family: 'Usual Regular';
            }

            #starter-how-to.hide {
                display: none;
            }

            #starter-how-to h3 {
                grid-column: 1 / 4;
                margin-bottom: 2rem;
                text-align: center;
                font-size: 2.2rem;
            }

            #starter-how-to .advice {
                padding: 0.75rem;
                border-radius: 0.375rem;
                background-color: rgb(247, 247, 248);
                font-size: 14px;
                text-align: center;
            }

            #starter-how-to .advice > strong {
                font-weight: bold;
            }

            @media screen and (max-width: 768px) {
                #starter-how-to {
                    top: 5%;
                    grid-template-columns: 1fr;
                    grid-row-gap: .8rem;
                    margin: 0 20px;
                }

                #starter-how-to h3 {
                    grid-column: 1 / 2;
                    margin-bottom: 1rem;
                }
            }
        </style>
    </head>
    <body>
        <section class="page-container">

            <header class="header">
                <!-- Header bar -->
                <?php insert_html('header_bar') ?>


                <section class="header-title">
                    <h1 class="title-searched heading-3" style="visibility: hidden;">
                        AI-powered search
                    </h1>
                    <h1 class="title-results heading-3">
                        AI-powered search
                    </h1>
                </section>
            </header>


            <!-- Mobile bar -->
            <?php insert_html('mobile_nav') ?>

            <section class="chat-container">
                <div id="starter-how-to">
                    <h3>How to use</h3>
                    <p class="advice">A <strong>longer</strong> question provides more context and information, enhancing the likelihood of receiving precise answer.</p>
                    <p class="advice">Including as many <strong>relevant</strong> keywords as possible greatly improves the quality and accuracy of the answer.</p>
                    <p class="advice">A more <strong>specific</strong> question ensures a focused and targeted response, and increasing the relevance of the answer provided.</p>
                </div>
                <div id="spacer"></div>
                
                <form class="prompt-form">
                    <input type="hidden" id="csrf_token" value="<?php echo $_SESSION['csrf_token']; ?>">

                    <div class="dot-animation">
                        <div class="dot first"></div>
                        <div class="dot second"></div>
                        <div class="dot third"></div>
                    </div>

                    <fieldset>
                        <div>
                            <span id="js-prompt-text" class="textarea" role="textbox" contenteditable></span>
                        </div>
                        <button id="js-prompt-submit">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none" class="h-4 w-4" stroke-width="2">
                                <path d="M.5 1.163A1 1 0 0 1 1.97.28l12.868 6.837a1 1 0 0 1 0 1.766L1.969 15.72A1 1 0 0 1 .5 14.836V10.33a1 1 0 0 1 .816-.983L8.5 8 1.316 6.653A1 1 0 0 1 .5 5.67V1.163Z" fill="currentColor"></path>
                            </svg>
                        </button>
                    </fieldset>

                    <small>&copy; Tesla Center <?php echo date("Y"); ?>. All rights reserved.</small>
                </form>
            </section>
        </section>
    </body>
</html>