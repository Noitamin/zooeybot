import json
import unittest
from unittest.mock import patch

from test_conversations import Channel, message
from test_websearch import chatbot, Context
from utils.messagehistory import summary_history


class SummaryTests(unittest.IsolatedAsyncioTestCase):
    async def test_default_count_order_and_request_excluded(self):
        channel = Channel()
        channel.messages = [message(channel, i, f'message {i}', bot=i % 2 == 0) for i in range(50, 0, -1)]
        incoming = message(channel, 51, 'summarize')
        result = await summary_history(incoming)
        self.assertEqual(channel.history_options, {'limit': 40, 'before': incoming})
        self.assertEqual(result['returned_count'], 40)
        self.assertEqual(result['messages'][0]['text'], 'message 11')
        self.assertEqual(result['messages'][-1]['text'], 'message 50')

    async def test_short_history_truncation_and_attachments(self):
        channel = Channel()
        previous = message(channel, 1, 'x' * 5000)
        previous.attachments = [object()]
        channel.messages = [previous]
        result = await summary_history(message(channel, 2, 'summarize'), 50)
        self.assertEqual(result['requested_count'], 50)
        self.assertEqual(result['returned_count'], 1)
        self.assertTrue(result['text_truncated'])
        self.assertEqual(result['messages'][0]['attachments'], 1)
        self.assertLess(len(result['messages'][0]['text']), 1000)

    async def test_invalid_counts_permission_failure_and_empty_channel(self):
        channel = Channel()
        incoming = message(channel, 1, 'summarize')
        for count in (0, 201, True, '20', 2.5):
            self.assertIn('error', await summary_history(incoming, count))
        self.assertIsNone(channel.history_options)
        self.assertEqual((await summary_history(incoming))['returned_count'], 0)
        channel.history_error = True
        self.assertIn('Read Message History', (await summary_history(incoming))['error'])

    async def test_threaded_tool_fetches_current_channel_without_persisting_history(self):
        channel = Channel()
        channel.messages = [message(channel, 1, 'background only')]
        ctx = Context()
        ctx.channel = channel
        ctx.message = message(channel, 2, 'summarize')
        cog = chatbot.ChatBot(None)
        seen = []
        def completion(request, *, summary_reader):
            result = summary_reader(20)
            seen.append(result)
            return 'A concise summary, mortal.'
        with patch.object(chatbot, 'completion_ds', side_effect=completion):
            await cog.respond(ctx, 'summarize')
        self.assertEqual(seen[0]['messages'][0]['text'], 'background only')
        self.assertNotIn('background only', json.dumps(list(cog.messages.values())))
        self.assertEqual(ctx.sent[0][0], 'A concise summary, mortal.')


if __name__ == '__main__':
    unittest.main()
