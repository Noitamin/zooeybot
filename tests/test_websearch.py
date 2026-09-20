import asyncio
import importlib
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

# Tests do not load real credentials or contact either provider.
with patch.dict(sys.modules, {
    'utils.settings': SimpleNamespace(TAVILY_API_KEY='test-key'),
    'utils.chatcompletion': SimpleNamespace(completion=Mock(), completion_ds=Mock(), completion_xai=Mock()),
}):
    websearch = importlib.import_module('utils.websearch')
    chatbot = importlib.import_module('cogs.chatbot')


class ProviderTests(unittest.TestCase):
    def test_basic_request_and_result_bounds(self):
        response = Mock(status_code=200)
        response.json.return_value = {'results': [
            {'url': 'https://example.com', 'title': 'Example', 'content': 'x' * 3000},
            {'url': 'javascript:bad', 'content': 'bad'},
        ]}
        with patch.object(websearch.requests, 'post', return_value=response) as post:
            results = websearch.search_web('question')
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0]['content']), 2000)
        self.assertEqual(post.call_args.kwargs['json']['search_depth'], 'basic')
        self.assertFalse(post.call_args.kwargs['json']['auto_parameters'])
        self.assertEqual(post.call_args.kwargs['timeout'], (5, 25))

    def test_missing_key_does_not_request(self):
        with patch.object(websearch, 'TAVILY_API_KEY', ''), patch.object(websearch.requests, 'post') as post:
            with self.assertRaisesRegex(websearch.SearchError, 'configured'):
                websearch.search_web('question')
            post.assert_not_called()

    def test_safe_errors(self):
        for status in [401, 429, 432, 433]:
            with self.subTest(status=status), patch.object(websearch.requests, 'post', return_value=Mock(status_code=status)):
                with self.assertRaises(websearch.SearchError):
                    websearch.search_web('question')
        with patch.object(websearch.requests, 'post', side_effect=websearch.requests.Timeout('secret')):
            with self.assertRaisesRegex(websearch.SearchError, 'timed out'):
                websearch.search_web('question')
        response = Mock(status_code=200)
        response.json.return_value = {'unexpected': []}
        with patch.object(websearch.requests, 'post', return_value=response):
            with self.assertRaises(websearch.SearchError):
                websearch.search_web('question')


class Typing:
    async def __aenter__(self): pass
    async def __aexit__(self, *args): pass


class Context:
    def __init__(self, guild=1, user=1):
        self.guild = SimpleNamespace(id=guild) if guild else None
        self.author = SimpleNamespace(id=user, display_name='User')
        self.channel = SimpleNamespace(typing=Typing)
        self.sent = []

    async def send(self, text, **kwargs):
        self.sent.append((text, kwargs))


class CommandTests(unittest.IsolatedAsyncioTestCase):
    async def test_chat_uses_deepseek_and_sends_long_search_answers(self):
        bot = chatbot.ChatBot(None)
        ctx = Context()
        answer = 'a' * 2100
        with patch.object(chatbot, 'completion_ds', return_value=answer) as complete:
            await bot.chat.callback(bot, ctx, message='latest news')
        complete.assert_called_once()
        self.assertEqual(''.join(text for text, _ in ctx.sent), answer)
        self.assertTrue(all(len(text) <= 2000 for text, _ in ctx.sent))
        self.assertEqual(bot.messages[('guild', 1)][-1]['content'], answer)

    async def test_natural_reply_memory_isolation_and_discord_limits(self):
        bot = chatbot.ChatBot(None)
        result = [{'title': 'Example', 'url': 'https://example.com', 'content': 'evidence'}]
        with patch.object(chatbot, 'search_web', return_value=result), patch.object(chatbot, 'completion_ds', return_value='a' * 2100) as complete:
            for guild in (1, 2):
                ctx = Context(guild)
                await bot.search.callback(bot, ctx, question=f'question {guild}')
                self.assertTrue(all(len(text) <= 2000 for text, _ in ctx.sent))
                self.assertEqual(''.join(text for text, _ in ctx.sent), 'a' * 2100)
                self.assertTrue(all(not options['allowed_mentions'].everyone for _, options in ctx.sent))
            self.assertNotIn('question 1', str(complete.call_args))
            for _ in range(12):
                await bot.search.callback(bot, Context(), question='again')
        self.assertEqual(len(bot.messages[('guild', 1)]), 21)
        self.assertEqual(bot.messages[('guild', 1)][0]['role'], 'system')
        await bot.chat.callback(bot, Context(), message='CLEAR')
        self.assertNotIn(('guild', 1), bot.messages)
        self.assertIn(('guild', 2), bot.messages)

    async def test_no_results_missing_key_and_invalid_query(self):
        bot = chatbot.ChatBot(None)
        for value in ([], websearch.SearchError('not configured')):
            ctx = Context()
            with patch.object(chatbot, 'search_web', side_effect=value if isinstance(value, Exception) else None, return_value=value), patch.object(chatbot, 'completion_ds') as complete:
                await bot.search.callback(bot, ctx, question='question')
                complete.assert_not_called()
                self.assertTrue(ctx.sent)
        for question in ('', 'x' * 1001):
            with patch.object(chatbot, 'search_web') as search:
                await bot.search.callback(bot, Context(), question=question)
                search.assert_not_called()
        self.assertFalse(bot.messages)

    async def test_dm_isolation(self):
        bot = chatbot.ChatBot(None)
        result = [{'title': '', 'url': 'https://example.com', 'content': 'evidence'}]
        with patch.object(chatbot, 'search_web', return_value=result), patch.object(chatbot, 'completion_ds', return_value='answer'):
            for user in (1, 2):
                await bot.search.callback(bot, Context(None, user), question='question')
        self.assertEqual(set(bot.messages), {('dm', 1), ('dm', 2)})


if __name__ == '__main__':
    unittest.main()
