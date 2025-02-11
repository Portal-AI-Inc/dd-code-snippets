<?php

declare(strict_types=1);

namespace App\Common\Intercom;

use App\Common\Accounts\Models\Account;
use App\Common\Conversations\Contacts\Forms\ContactForm;
use App\Common\Conversations\ConversationService;
use App\Common\Conversations\Forms\ConversationForm;
use App\Common\Conversations\Messages\MessageForm;
use App\Common\Conversations\Models\ConversationType;
use App\Common\Intercom\Models\AbstractConversationPart;
use App\Common\Intercom\Models\Author;
use App\Common\Intercom\Models\Conversation;

class IntercomService
{
    public function upsertConversation(Account $account, Conversation $conversation): \App\Common\Conversations\Models\Conversation
    {
        $conversationService = new ConversationService();

        $messageForms = [];
        foreach ($conversation->conversationParts as $conversationPart) {
            if (
                ($conversationPart->isEmpty() && !$conversationPart->getAttachmentUrls())
                || $conversationPart->isDeletedMessage()
                || $conversationPart->isTypeNote()
            ) {
                continue;
            }

            $contactForm = $this->convertAuthorToContactForm($account, $conversationPart->author);
            $messageForms[] = $this->convertConversationPartToMessageForm($account, $conversationPart,$contactForm);
        }

        if (!$messageForms) {
            $contactForm = $this->convertAuthorToContactForm($account, $conversation->author);
            $messageForms[] = $this->convertConversationPartToMessageForm($account, $conversation,$contactForm);
        }

        $conversationForm = $this->convertConversationToConversationForm($account, $conversation, $messageForms);
        if (!$conversationForm->validate()) {
            throw new \Exception('Validation failed: ' . json_encode($conversationForm->getErrors()));
        }

        $conversationPart = $conversationService->upsert($account, $conversationForm, ConversationType::intercom);

        return $conversationPart->conversation;
    }

    public function convertAuthorToContactForm(Account $account, Author $author): ContactForm
    {
        $contactForm = new ContactForm($account);
        $contactForm->external_id = $author->id;
        $contactForm->name = $author->name;
        $contactForm->email = $author->email;
        $contactForm->role = $author->getMessageRole();
        $contactForm->extra_data = $author->data;
        $contactForm->source_link = $author->getSourceLink();

        return $contactForm;
    }

    public function convertConversationPartToMessageForm(Account $account, AbstractConversationPart $conversationPart, ContactForm $contactForm): MessageForm
    {
        $messageForm = new MessageForm($account);
        $messageForm->external_id = $conversationPart->id;
        $messageForm->content = $conversationPart->body . $conversationPart->getAttachmentUrls();
        $messageForm->role = $conversationPart->author->getMessageRole();
        $messageForm->sent_at = $conversationPart->createdAt;
        $messageForm->extra_data = $conversationPart->data;
        $messageForm->contact = $contactForm;
        $messageForm->source_link = $conversationPart->getSourceLink();

        return $messageForm;
    }

    /**
     * @param Account $account
     * @param Conversation $conversation
     * @param MessageForm[] $messageForms
     *
     * @return ConversationForm
     */
    public function convertConversationToConversationForm(Account $account, Conversation $conversation, array $messageForms): ConversationForm
    {
        $conversationForm = new ConversationForm($account);
        $conversationForm->external_id = $conversation->id;
        $conversationForm->source_link = $conversation->getSourceLink();
        $conversationForm->messages = $messageForms;

        return $conversationForm;
    }
}