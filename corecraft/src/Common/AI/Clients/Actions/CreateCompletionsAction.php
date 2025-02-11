<?php

declare(strict_types=1);

namespace App\Common\AI\Clients\Actions;

use App\Common\Accounts\Models\Account;
use App\Common\AI\AIException;
use App\Common\AI\Clients\Anthropic\AnthropicClient;
use App\Common\AI\Clients\Core\AbstractResponse;
use App\Common\AI\Clients\Google\GoogleClient;
use App\Common\AI\Clients\OpenAI\OpenAIClient;
use App\Common\AI\Clients\Perplexity\PerplexityClient;
use App\Common\AI\Clients\Tools\ToolsHandlerInterface;
use App\Common\AI\Models\Request;
use App\Common\Conversations\Experiments\ExperimentService;
use App\Common\Conversations\Messages\Models\Message;
use App\Common\Conversations\Models\ConversationPart;
use GuzzleHttp\Exception\GuzzleException;
use Yii;

class CreateCompletionsAction extends AbstractAction
{
    public const MESSAGE_STUB = [['role' => Message::ROLE_USER, 'content' => '.']];

    public function __construct(
        Account $account,
        public string $model,
        public string $system,
        public array $messages = [],
        public array $tools = [],
        public int $toolCallCounter = 0,
        ?ConversationPart $conversationPart = null,
    ) {
        $client = match (true) {
            array_key_exists($this->model, AnthropicClient::MODELS_PRICES) => new AnthropicClient(),
            array_key_exists($this->model, OpenAIClient::MODELS_PRICES) => new OpenAIClient(),
            array_key_exists($this->model, PerplexityClient::MODELS_PRICES) => new PerplexityClient(),
            array_key_exists($this->model, GoogleClient::MODELS_PRICES) => new GoogleClient(),
            default => throw new AIException(AIException::ERROR_CODE_UNEXPECTED_AI_MODEL)
        };

        if (!$this->messages) {
            $this->messages = self::MESSAGE_STUB;
        }

        $requestClass = match(true) {
            $client instanceof AnthropicClient => \App\Common\AI\Clients\Anthropic\CreateCompletion\CreateCompletionRequest::class,
            $client instanceof OpenAIClient => \App\Common\AI\Clients\OpenAI\CreateCompletion\CreateCompletionRequest::class,
            $client instanceof PerplexityClient => \App\Common\AI\Clients\Perplexity\CreateCompletion\CreateCompletionRequest::class,
            $client instanceof GoogleClient => \App\Common\AI\Clients\Google\CreateCompletion\CreateCompletionRequest::class,
        };

        $tools = [];
        foreach ($this->tools as $toolName) {
            $toolConfig = match(true) {
                $client instanceof AnthropicClient => match ($toolName) {
                    \App\Common\AI\Clients\Anthropic\CreateCompletion\Tools\CallPromptTool::getName() => \App\Common\AI\Clients\Anthropic\CreateCompletion\Tools\CallPromptTool::getConfig(),
                    \App\Common\AI\Clients\Anthropic\CreateCompletion\Tools\SearchWebTool::getName() => \App\Common\AI\Clients\Anthropic\CreateCompletion\Tools\SearchWebTool::getConfig(),
                    \App\Common\AI\Clients\Anthropic\CreateCompletion\Tools\DatasetSearchTool::getName() => \App\Common\AI\Clients\Anthropic\CreateCompletion\Tools\DatasetSearchTool::getConfig(),
                    \App\Common\AI\Clients\Anthropic\CreateCompletion\Tools\DatasetQueryTool::getName() => \App\Common\AI\Clients\Anthropic\CreateCompletion\Tools\DatasetQueryTool::getConfig(),
                    \App\Common\AI\Clients\Anthropic\CreateCompletion\Tools\BrowseWebTool::getName() => \App\Common\AI\Clients\Anthropic\CreateCompletion\Tools\BrowseWebTool::getConfig(),
                    \App\Common\AI\Clients\Anthropic\CreateCompletion\Tools\RetrieveWebTool::getName() => \App\Common\AI\Clients\Anthropic\CreateCompletion\Tools\RetrieveWebTool::getConfig(),
                    \App\Common\AI\Clients\Anthropic\CreateCompletion\Tools\ParseFileTool::getName() => \App\Common\AI\Clients\Anthropic\CreateCompletion\Tools\ParseFileTool::getConfig(),
                    \App\Common\AI\Clients\Anthropic\CreateCompletion\Tools\IntercomReplyToTool::getName() => \App\Common\AI\Clients\Anthropic\CreateCompletion\Tools\IntercomReplyToTool::getConfig(),
                    \App\Common\AI\Clients\Anthropic\CreateCompletion\Tools\ImageAnalysisTool::getName() => \App\Common\AI\Clients\Anthropic\CreateCompletion\Tools\ImageAnalysisTool::getConfig(),
                    default => throw new AIException(AIException::ERROR_CODE_UNEXPECTED_TOOL)
                },
                $client instanceof OpenAIClient => match ($toolName) {
                    \App\Common\AI\Clients\OpenAI\CreateCompletion\Tools\CallPromptTool::getName() => \App\Common\AI\Clients\OpenAI\CreateCompletion\Tools\CallPromptTool::getConfig(),
                    \App\Common\AI\Clients\OpenAI\CreateCompletion\Tools\SearchWebTool::getName() => \App\Common\AI\Clients\OpenAI\CreateCompletion\Tools\SearchWebTool::getConfig(),
                    \App\Common\AI\Clients\OpenAI\CreateCompletion\Tools\DatasetSearchTool::getName() => \App\Common\AI\Clients\OpenAI\CreateCompletion\Tools\DatasetSearchTool::getConfig(),
                    \App\Common\AI\Clients\OpenAI\CreateCompletion\Tools\DatasetQueryTool::getName() => \App\Common\AI\Clients\OpenAI\CreateCompletion\Tools\DatasetQueryTool::getConfig(),
                    \App\Common\AI\Clients\OpenAI\CreateCompletion\Tools\BrowseWebTool::getName() => \App\Common\AI\Clients\OpenAI\CreateCompletion\Tools\BrowseWebTool::getConfig(),
                    \App\Common\AI\Clients\OpenAI\CreateCompletion\Tools\RetrieveWebTool::getName() => \App\Common\AI\Clients\OpenAI\CreateCompletion\Tools\RetrieveWebTool::getConfig(),
                    \App\Common\AI\Clients\OpenAI\CreateCompletion\Tools\ParseFileTool::getName() => \App\Common\AI\Clients\OpenAI\CreateCompletion\Tools\ParseFileTool::getConfig(),
                    \App\Common\AI\Clients\OpenAI\CreateCompletion\Tools\IntercomReplyToTool::getName() => \App\Common\AI\Clients\OpenAI\CreateCompletion\Tools\IntercomReplyToTool::getConfig(),
                    \App\Common\AI\Clients\OpenAI\CreateCompletion\Tools\ImageAnalysisTool::getName() => \App\Common\AI\Clients\OpenAI\CreateCompletion\Tools\ImageAnalysisTool::getConfig(),
                    default => throw new AIException(AIException::ERROR_CODE_UNEXPECTED_TOOL)
                },
                $client instanceof GoogleClient => match ($toolName) {
                    \App\Common\AI\Clients\Google\CreateCompletion\Tools\CallPromptTool::getName() => \App\Common\AI\Clients\Google\CreateCompletion\Tools\CallPromptTool::getConfig(),
                    \App\Common\AI\Clients\Google\CreateCompletion\Tools\SearchWebTool::getName() => \App\Common\AI\Clients\Google\CreateCompletion\Tools\SearchWebTool::getConfig(),
                    \App\Common\AI\Clients\Google\CreateCompletion\Tools\DatasetSearchTool::getName() => \App\Common\AI\Clients\Google\CreateCompletion\Tools\DatasetSearchTool::getConfig(),
                    \App\Common\AI\Clients\Google\CreateCompletion\Tools\DatasetQueryTool::getName() => \App\Common\AI\Clients\Google\CreateCompletion\Tools\DatasetQueryTool::getConfig(),
                    \App\Common\AI\Clients\Google\CreateCompletion\Tools\BrowseWebTool::getName() => \App\Common\AI\Clients\Google\CreateCompletion\Tools\BrowseWebTool::getConfig(),
                    \App\Common\AI\Clients\Google\CreateCompletion\Tools\RetrieveWebTool::getName() => \App\Common\AI\Clients\Google\CreateCompletion\Tools\RetrieveWebTool::getConfig(),
                    \App\Common\AI\Clients\Google\CreateCompletion\Tools\ParseFileTool::getName() => \App\Common\AI\Clients\Google\CreateCompletion\Tools\ParseFileTool::getConfig(),
                    \App\Common\AI\Clients\Google\CreateCompletion\Tools\IntercomReplyToTool::getName() => \App\Common\AI\Clients\Google\CreateCompletion\Tools\IntercomReplyToTool::getConfig(),
                    \App\Common\AI\Clients\Google\CreateCompletion\Tools\ImageAnalysisTool::getName() => \App\Common\AI\Clients\Google\CreateCompletion\Tools\ImageAnalysisTool::getConfig(),
                    default => throw new AIException(AIException::ERROR_CODE_UNEXPECTED_TOOL)
                },
                default => null
            };

            if ($toolConfig) {
                $tools[] = $toolConfig;
            }
        }

        $request = new $requestClass(
            system: $this->system,
            messages: $this->messages,
            model: $this->model,
            tools: $tools
        );

        parent::__construct($account, $client, $request, $conversationPart);
    }

    public static function getName(): string
    {
        return 'create_completions';
    }

    public function enqueueRun(): void
    {
        $queue = match(true) {
            $this->client instanceof AnthropicClient => Yii::$app->claudeClientQueue,
            $this->client instanceof OpenAIClient => Yii::$app->openAIClientQueue,
            $this->client instanceof PerplexityClient => Yii::$app->perplexityClientQueue,
            $this->client instanceof GoogleClient => Yii::$app->googleClientQueue,
            default => throw new AIException(AIException::ERROR_CODE_UNEXPECTED_AI_MODEL)
        };

        (new CreateCompletionJob())->push(
            $queue,
            $this->account->account_id,
            $this->model,
            $this->system,
            $this->messages,
            $this->tools,
            $this->conversationPart?->id
        );
    }

    protected function executeRequest(): AbstractResponse
    {
        return $this->client->createCompletion($this->request);
    }

    /**
     * @throws GuzzleException
     */
    protected function handleResponse(AbstractResponse $response, Request $requestLog): AbstractResponse
    {
        $toolCallCounter = $this->toolCallCounter + 1;
        if ($this->toolCallCounter >= ToolsHandlerInterface::MAX_TOOL_CALLS) {
            throw new AIException(AIException::ERROR_CODE_TOOL_CALLS_REACHED_LIMIT);
        }

        $toolHandler = match (true) {
            $response instanceof \App\Common\AI\Clients\Anthropic\CreateCompletion\CreateCompletionResponse =>
            new \App\Common\AI\Clients\Anthropic\CreateCompletion\Tools\ToolsHandler(
                $this->account,
                $this->model,
                $this->system,
                $this->messages,
                $this->tools,
                $response,
                $toolCallCounter,
                $this->conversationPart
            ),
            $response instanceof \App\Common\AI\Clients\OpenAI\CreateCompletion\CreateCompletionResponse =>
            new \App\Common\AI\Clients\OpenAI\CreateCompletion\Tools\ToolsHandler(
                $this->account,
                $this->model,
                $this->system,
                $this->messages,
                $this->tools,
                $response,
                $toolCallCounter,
                $this->conversationPart
            ),
            $response instanceof \App\Common\AI\Clients\Google\CreateCompletion\CreateCompletionResponse =>
            new \App\Common\AI\Clients\Google\CreateCompletion\Tools\ToolsHandler(
                $this->account,
                $this->model,
                $this->system,
                $this->messages,
                $this->tools,
                $response,
                $toolCallCounter,
                $this->conversationPart
            ),
            default => null
        };

        if ($toolHandler) {
            $response = $toolHandler->handle();
        }

        (new ExperimentService())->handleAIResponse($requestLog, $response->content);

        return $response;
    }
}