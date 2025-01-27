from langchain_community.llms import OpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from .. import const
from .model_factory import ModelFactory


class OpenAIFactory(ModelFactory):
    def __init__(self, llm_config):
        self.model = llm_config[const.CONFIG_MODEL]
        if not self.model:
            raise ValueError(f'Missing {const.CONFIG_MODEL} in llm config')
        self.api_key = llm_config[const.CONFIG_LLM_OPENAI_API_KEY]
        if not self.api_key:
            raise ValueError(f'Missing {const.CONFIG_LLM_OPENAI_API_KEY} in llm config')

    def create_llm(self):
        return OpenAI(
            openai_api_key=self.api_key,
            model_name=self.model,
        )

    def create_embeddings(self) -> OpenAIEmbeddings:
        return OpenAIEmbeddings(model=self.model, openai_api_key=self.api_key)
