<?php

declare(strict_types=1);

namespace App\Common\Intercom;

use App\Common\Accounts\Models\AccountSettings\IntercomIntegration\IntercomIntegration;
use App\Common\Core\BaseClient\AbstractClient;
use App\Common\Intercom\Models\Conversation;
use App\Common\Intercom\Requests\AbstractSendReplyRequest;
use GuzzleHttp\Client;
use yii\helpers\Json;

class IntercomClient extends AbstractClient
{
    public const BASE_URL = 'https://api.intercom.io/';
    public const TIMEOUT = 90;
    public const CONNECT_TIMEOUT = 50;

    private Client $guzzleClient;

    public function __construct(public IntercomIntegration $intercomIntegration)
    {
        $this->guzzleClient = new Client(
            [
                'base_uri' => self::BASE_URL,
                'timeout' => self::TIMEOUT,
                'connect_timeout' => self::CONNECT_TIMEOUT,
                'headers' => [
                    'Accept' => 'application/json',
                    'Authorization' => 'Bearer ' . $this->intercomIntegration->token,
                    'Intercom-Version' => '2.9',
                ],
            ]
        );
    }

    public static function getConversationUrl(string $appId, string $conversationId, ?string $conversationPartId = null): string
    {
        return sprintf(
            'https://app.intercom.com/a/inbox/%s/inbox/conversation/%s%s',
            $appId,
            $conversationId,
            $conversationPartId ? sprintf('#part_id=comment-%s-%s', $conversationId, $conversationPartId) : '',
        );
    }

    public static function getAuthorUrl(string $appId, string $conversationId, ?string $conversationPartId = null): string
    {
        return sprintf(
            'https://app.intercom.com/a/inbox/%s/inbox/conversation/%s%s',
            $appId,
            $conversationId,
            $conversationPartId ? sprintf('#part_id=comment-%s-%s', $conversationId, $conversationPartId) : '',
        );
    }

    public function getConversation(string $id, array $params = ['display_as' => 'plaintext']): Conversation
    {
        $response = $this->guzzleClient->get(
            "/conversations/$id",
            [
                'query' => $params,
            ]
        );

        $conversationData = Json::decode($response->getBody()->getContents());

        return Conversation::fillFromArray($this->intercomIntegration->appId, $conversationData);
    }

    public function replyToConversation(AbstractSendReplyRequest $request): Conversation
    {
        $response = $this->guzzleClient->post(
            "/conversations/$request->conversationId/reply",
            ['form_params' => $request->toArray()]
        );
        $conversationData = Json::decode($response->getBody()->getContents());

        return Conversation::fillFromArray($this->intercomIntegration->appId, $conversationData);
    }
}