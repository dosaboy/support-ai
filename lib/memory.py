from operator import itemgetter
from threading import Lock
from langchain.memory import ConversationSummaryBufferMemory, MongoDBChatMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableLambda, RunnablePassthrough
from lib.const import CONFIG_DB_CONNECTION

class Memory:
    def __init__(self, config, llm):
        if CONFIG_DB_CONNECTION not in config:
            raise ValueError(f'The config doesn\'t contain {CONFIG_DB_CONNECTION}')
        self.db_connection = config[CONFIG_DB_CONNECTION]
        self.llm = llm
        self.mutex = Lock()
        self.session_memories = {}

    def __get_session_memory(self, session):
        with self.mutex:
            if session not in self.session_memories:
                memory = MongoDBChatMessageHistory(
                        connection_string=self.db_connection,
                        session_id=session
                        )
                self.session_memories[session] = ConversationSummaryBufferMemory(chat_memory=memory,
                                                                                 llm=self.llm,
                                                                                 return_messages=True
                                                                                 )
            return self.session_memories[session]

    def integrate(self, session, query, context):
        memory = self.__get_session_memory(session)
        prompt = ChatPromptTemplate.from_messages([
            ('system', 'You are a helpful chatbot'),
            MessagesPlaceholder(variable_name='history'),
            ('human', 'Based on the context: {context}, {query}'),
            ])
        chain = (
                RunnablePassthrough.assign(
                    history=RunnableLambda(memory.load_memory_variables) | itemgetter('history')
                    )
                | prompt
                | self.llm
                | StrOutputParser()
                )
        integrated_context = chain.invoke({'context': context, 'query': query})
        memory.save_context({'input': query}, {'output': integrated_context})
        return integrated_context

    def clear(self, session):
        with self.mutex:
            memory = MongoDBChatMessageHistory(
                    connection_string=self.db_connection,
                    session_id=session
                    )
            ConversationSummaryBufferMemory(chat_memory=memory).clear()
            if session in self.session_memories:
                del self.session_memories[session]
