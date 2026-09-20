import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from openai.types.chat import ChatCompletionMessage

spec = importlib.util.spec_from_file_location('tested_chatcompletion', Path(__file__).resolve().parents[1] / 'utils/chatcompletion.py')
completion = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {
    'utils.settings': SimpleNamespace(OPENAI_KEY='test', DEEPSEEK_KEY='test', XAI_API_KEY='test'),
    'utils.websearch': SimpleNamespace(SearchError=type('SearchError', (Exception,), {}), TAVILY_API_KEY='test', search_web=Mock()),
}):
    spec.loader.exec_module(completion)


def reply(content=None, calls=None):
    return SimpleNamespace(choices=[SimpleNamespace(message=ChatCompletionMessage(
        role='assistant', content=content, tool_calls=calls,
    ))])


def call(number, arguments='{"query": "latest information"}'):
    return {'id': f'call_{number}', 'type': 'function', 'function': {'name': 'web_search', 'arguments': arguments}}


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.history = [{'role': 'system', 'content': 'persona'}, {'role': 'user', 'content': 'question'}]
        self.result = [{'url': 'https://example.com', 'title': 'Example', 'content': 'Evidence'}]

    def test_tool_roundtrip_natural_reply_and_history_unchanged(self):
        requests = []
        responses = iter([reply(calls=[call(1)]), reply('This news is quite lit, mortal.')])
        def create(**kwargs):
            requests.append({**kwargs, 'messages': list(kwargs['messages'])})
            return next(responses)
        with patch.object(completion.ds_client.chat.completions, 'create', side_effect=create), patch.object(completion, 'search_web', return_value=self.result) as search:
            answer = completion.completion_ds(self.history)
        search.assert_called_once_with('latest information')
        self.assertEqual(answer, 'This news is quite lit, mortal.')
        self.assertEqual(len(self.history), 2)
        self.assertEqual(requests[0]['tool_choice'], 'auto')
        tool = requests[1]['messages'][-1]
        self.assertEqual(tool['role'], 'tool')
        self.assertEqual(tool['tool_call_id'], 'call_1')
        self.assertIn('https://example.com', tool['content'])

    def test_no_search_needed(self):
        with patch.object(completion.ds_client.chat.completions, 'create', return_value=reply('Hello')), patch.object(completion, 'search_web') as search:
            self.assertEqual(completion.completion_ds(self.history), 'Hello')
            search.assert_not_called()

    def test_lookup_promise_is_completed_before_returning(self):
        promise = 'Time is a construct mortals cling to... but fine, I shall consult the ether.'
        with patch.object(completion.ds_client.chat.completions, 'create', side_effect=[
            reply(promise), reply('I shall search.', calls=[call(1)]), reply('Here is the answer, mortal.'),
        ]) as create, patch.object(completion, 'search_web', return_value=self.result) as search:
            self.assertEqual(completion.completion_ds(self.history), 'Here is the answer, mortal.')
        self.assertEqual(create.call_count, 3)
        search.assert_called_once()
        self.assertEqual(len(self.history), 2)

    def test_repeated_lookup_promise_has_bounded_retry(self):
        with patch.object(completion.ds_client.chat.completions, 'create', return_value=reply("I'll look it up.")) as create:
            answer = completion.completion_ds(self.history)
        self.assertEqual(create.call_count, 2)
        self.assertIn('cannot verify', answer)

    def test_completed_answer_and_past_lookup_are_not_retried(self):
        for answer in ('I checked: the answer is 42.', "I'll check. The answer is 42."):
            with patch.object(completion.ds_client.chat.completions, 'create', return_value=reply(answer)) as create:
                self.assertEqual(completion.completion_ds(self.history), answer)
                create.assert_called_once()

    def test_missing_key_and_explicit_disable(self):
        for enabled, key in ((True, ''), (False, 'test')):
            with patch.object(completion, 'TAVILY_API_KEY', key), patch.object(completion.ds_client.chat.completions, 'create', return_value=reply('Answer')) as create:
                completion.completion_ds(self.history, allow_search=enabled)
                self.assertNotIn('tools', create.call_args.kwargs)

    def test_search_budget_including_parallel_calls(self):
        with patch.object(completion.ds_client.chat.completions, 'create', side_effect=[reply(calls=[call(i) for i in range(5)]), reply('Answer')]) as create, patch.object(completion, 'search_web', return_value=self.result) as search:
            completion.completion_ds(self.history)
        self.assertEqual(search.call_count, 3)
        self.assertEqual(create.call_args.kwargs['tool_choice'], 'none')
        self.assertEqual(len([m for m in create.call_args.kwargs['messages'] if m['role'] == 'tool']), 5)

    def test_errors_are_returned_to_model(self):
        for arguments, failure in (('not json', None), ('[]', None), ('{"query":""}', None), ('{"query":"question"}', completion.SearchError('Limit reached'))):
            with self.subTest(arguments=arguments, failure=failure), patch.object(completion.ds_client.chat.completions, 'create', side_effect=[reply(calls=[call(1, arguments)]), reply('Unable to verify')]) as create, patch.object(completion, 'search_web', side_effect=failure, return_value=[]):
                self.assertEqual(completion.completion_ds(self.history), 'Unable to verify')
                self.assertIn('error', create.call_args.kwargs['messages'][-1]['content'])


if __name__ == '__main__':
    unittest.main()
