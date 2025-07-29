
import logging
from typing import Dict

from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from webexpythonsdk.models.cards import TextBlock, FontWeight, FontSize, \
    Column, AdaptiveCard, ColumnSet, Choice, ChoiceSet, Submit
import webexpythonsdk.models.cards.options as OPTIONS

from formatting import quote_info, quote_warning
from models.command import Command
from models.response import response_from_adaptive_card
from commands.lite_llm import LiteLLM

log = logging.getLogger(__name__)

#######################
# default LLM configs #
#######################
lite_llm_url = "http://apollo.home:4000"
llm_model = "gpt-4o"
TEMPERATURE = 0.5


class LLM_Chat_Command(Command):

    def __init__(self, api_key, session_id="default"):

        super().__init__(
            command_keyword="/chat",
            help_message="Interact with LLM",
            chained_commands=[LLM_Chat_Callback()])

        self.api_key = api_key
        self.session_id = session_id

        self.session_histories: Dict[str, ChatMessageHistory] = {}

        if session_id not in self.session_histories:
            self.session_histories[session_id] = ChatMessageHistory()

        self.context = """
You are an intelligent assistant integrated into a Webex space.
You help users by answering technical and non-technical questions in a clear, concise, and professional manner.
Respond using plain language, unless a technical explanation is explicitly requested.
If the question is vague, politely ask for clarification.
If you are unsure or lack enough information, say so rather than guessing.
When applicable, format responses with lists, code blocks, or bullet points to enhance readability.
Avoid unnecessary repetition or conversational filler.
Your goal is to be helpful, respectful, and accurate within the context of a team chat environment.
        """


    def execute(self, prompt, attachment_actions, activity):

        prompt = prompt.strip()

        if not prompt:
            return self.show_llm_config_card()

        log.info("Got message prompt from user: '%s'", prompt)

        custom_prompt = ChatPromptTemplate.from_template("""
            Context:
            {context}

            Question:
            {question}

            Answer:
        """)

        litellm_obj = LiteLLM(lite_llm_url, self.api_key)
        if not litellm_obj.is_reachable():
            return quote_warning(f"LiteLLM is not reachable at {lite_llm_url}")

        if not litellm_obj.is_available(llm_model):
            return quote_warning(f"LLM model {llm_model} is not available")

        llm = ChatOpenAI(base_url=lite_llm_url,
                         model=llm_model,
                         temperature=TEMPERATURE)

        llm_chain = custom_prompt | llm

        chain_with_memory = RunnableWithMessageHistory(
            llm_chain,
            lambda sid: self.session_histories[sid],
            input_messages_key="question",
            history_messages_key="chat_history",
        )

        result = chain_with_memory.invoke(
            {
                "question": prompt,
                "context": self.context
            },
            config={"configurable": {"session_id": self.session_id}}
        )

        if isinstance(result, AIMessage):
            return quote_info(result.content)

        return quote_warning("Was expecting an AIMessage.")


    def show_llm_config_card(self):

        text1 = TextBlock("LLM Chat Config",
                          weight=FontWeight.BOLDER,
                          size=FontSize.MEDIUM)

        text2 = TextBlock("Fill out the form and click submit.",
                          wrap=True,
                          isSubtle=True)

        column_1 = Column(items=[text1, text2], width=2)

        column_set_1 = ColumnSet(columns=[column_1])

        ######

        text = TextBlock("LLM Model:",
                         wrap=True,
                         isSubtle=False)

        litellm_obj = LiteLLM(lite_llm_url, self.api_key)
        if not litellm_obj.is_reachable():
            return quote_warning("LiteLLM is not reachable")

        llm_models = litellm_obj.list_models()

        choices = []
        for status in llm_models:
            choices.append(Choice(status, status))

        default_model = str(llm_model) if llm_model in llm_models else ""

        choices_obj = ChoiceSet(id="llm_model",
                                isMultiSelect=False,
                                value=default_model,
                                choices=choices)

        choices_column = Column(items=[text, choices_obj], width=2)

        column_set_2 = ColumnSet(columns=[choices_column])

        ######

        text_temp = TextBlock("Temperature:",
                              wrap=True,
                              isSubtle=False)

        global TEMPERATURE

        temperature_choices = ChoiceSet(
            id="temperature",
            isMultiSelect=False,
            style=OPTIONS.ChoiceInputStyle.COMPACT,
            value=str(TEMPERATURE),
            choices=[
                Choice("0.0 (Deterministic)", "0.0"),
                Choice("0.2", "0.2"),
                Choice("0.5", "0.5"),
                Choice("0.7 (Balanced)", "0.7"),
                Choice("1.0 (Creative)", "1.0"),
            ]
        )

        temperature_column = Column(items=[text_temp, temperature_choices], width=2)
        column_set_3 = ColumnSet(columns=[temperature_column])

        ######

        submit = Submit(title="Submit",
                        data={"callback_keyword": "llm_callback"})

        card = AdaptiveCard(body=[column_set_1, column_set_2, column_set_3],
                            actions=[submit])

        return response_from_adaptive_card(card)


class LLM_Chat_Callback(Command):

    def __init__(self):

        super().__init__(card_callback_keyword="llm_callback",
                         delete_previous_message=False)


    def execute(self, message, attachment_actions, activity):

        all_inputs = attachment_actions.inputs

        global llm_model
        global TEMPERATURE

        llm_model_user = all_inputs.get("llm_model", None)
        if llm_model_user:
            llm_model = llm_model_user

        temperature_user = all_inputs.get("temperature", None)
        if temperature_user:
            TEMPERATURE = temperature_user

        return quote_info(f"LLM model is set to '{llm_model}', Temperature is set to '{TEMPERATURE}'")
