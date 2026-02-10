import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Mock env vars before importing logic that might use them at module level (though our logic puts them in functions)
with patch.dict(os.environ, {"OPENAI_API_KEY": "dummy-key"}):
    from src.utils.embeddings import get_embedding_model, compute_embeddings, compute_query_embedding

class TestEmbeddings(unittest.TestCase):

    @patch('src.utils.embeddings.SentenceTransformer')
    def test_get_embedding_model_local(self, mock_sentence_transformer):
        with patch.dict(os.environ, {"EMBEDDING_PROVIDER": "local"}):
            model = get_embedding_model()
            mock_sentence_transformer.assert_called_with("all-MiniLM-L12-v2")
            self.assertIsNotNone(model)

    @patch('src.utils.embeddings.OpenAIEmbeddings')
    def test_get_embedding_model_openai(self, mock_openai):
        with patch.dict(os.environ, {"EMBEDDING_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test"}):
            model = get_embedding_model()
            mock_openai.assert_called_with(model="text-embeddings-ada-002", openai_api_key="sk-test")
            self.assertIsNotNone(model)

    def test_compute_embeddings_local(self):
        mock_model = MagicMock()
        mock_model.encode.return_value.tolist.return_value = [[0.1, 0.2]]
        
        with patch.dict(os.environ, {"EMBEDDING_PROVIDER": "local"}):
            result = compute_embeddings(mock_model, ["text"])
            mock_model.encode.assert_called_with(["text"])
            self.assertEqual(result, [[0.1, 0.2]])

    def test_compute_embeddings_openai(self):
        mock_model = MagicMock()
        mock_model.embed_documents.return_value = [[0.1, 0.2]]
        
        with patch.dict(os.environ, {"EMBEDDING_PROVIDER": "openai"}):
            result = compute_embeddings(mock_model, ["text"])
            mock_model.embed_documents.assert_called_with(["text"])
            self.assertEqual(result, [[0.1, 0.2]])

if __name__ == '__main__':
    unittest.main()
