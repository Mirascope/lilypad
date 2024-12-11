"""Tests for the prompt decorator and related functionality"""


# @pytest.fixture
# def mock_prompt() -> PromptPublic:
#     """Fixture that returns a mock VersionPublic instance"""
#     return PromptPublic(
#         uuid=uuid4(),
#         hash="test_hash",
#         template="Recommend a {genre} book.",
#         provider=Provider.OPENAI,
#         model="gpt-4",
#         call_params=OpenAICallParams(
#             max_tokens=300,
#             temperature=0.7,
#             top_p=1.0,
#             frequency_penalty=0.0,
#             presence_penalty=0.0,
#             response_format=ResponseFormat(type="text"),
#             stop=None,
#         ),
#     )


# @pytest.fixture
# def mock_prompt_client(mock_prompt: PromptPublic):
#     """Fixture that mocks the prompt module's LilypadClient"""
#     with patch("lilypad.prompts.lilypad_client") as mock:
#         mock.get_prompt_active_version.return_value = mock_version
#         yield mock


# @pytest.fixture
# def mock_create_mirascope_call():
#     """Fixture that mocks the create_mirascope_call function"""
#     with patch("lilypad.prompts.create_mirascope_call") as mock:

#         def side_effect(fn, prompt, trace_decorator):
#             if inspect.iscoroutinefunction(fn):

#                 async def mock_async_fn(*args, **kwargs):
#                     return "Mocked book recommendation"

#                 return mock_async_fn
#             else:

#                 def mock_fn(*args, **kwargs):
#                     return "Mocked book recommendation"

#                 return mock_fn

#         mock.side_effect = side_effect
#         yield mock


# def test_recommend_book_sync(mock_prompt_client, mock_create_mirascope_call):
#     """Test synchronous book recommendation function"""

#     @prompt()
#     def recommend_book(genre: str) -> str:
#         return f"Recommend a {genre} book"

#     response = recommend_book("fantasy")
#     assert isinstance(response, str)
#     assert response == "Mocked book recommendation"
#     mock_prompt_client.get_prompt_active_version.assert_called_once()
#     mock_create_mirascope_call.assert_called()


# @pytest.mark.asyncio
# async def test_recommend_book_async(mock_prompt_client, mock_create_mirascope_call):
#     """Test asynchronous book recommendation function"""

#     @prompt()
#     async def recommend_book(genre: str) -> str:
#         return f"Recommend a {genre} book"

#     response = await recommend_book("science fiction")
#     assert isinstance(response, str)
#     mock_prompt_client.get_prompt_active_version.assert_called_once()
#     mock_create_mirascope_call.assert_called()


# def test_recommend_book_with_middleware(mock_prompt_client, mock_create_mirascope_call):
#     """Test book recommendation function with middleware"""
#     tracking = []

#     def track_recommendations(fn: Callable) -> Callable:
#         def wrapper(*args: Any, **kwargs: Any) -> str:
#             tracking.append({"genre": args[0] if args else kwargs.get("genre")})
#             result = fn(*args, **kwargs)
#             return str(result)

#         return wrapper

#     @track_recommendations
#     @prompt()
#     def recommend_book(genre: str) -> str:
#         return f"Recommend a {genre} book"

#     response = recommend_book("mystery")
#     assert isinstance(response, str)
#     assert response == "Mocked book recommendation"
#     assert len(tracking) == 1
#     assert tracking[0]["genre"] == "mystery"
#     mock_prompt_client.get_prompt_active_version.assert_called_once()
#     mock_create_mirascope_call.assert_called()


# def test_recommend_book_performance(mock_prompt_client, mock_create_mirascope_call):
#     """Test performance of book recommendation function"""

#     @prompt()
#     def recommend_book(genre: str) -> str:
#         return f"Recommend a {genre} book"

#     num_calls = 5
#     for _ in range(num_calls):
#         response = recommend_book("quick recommendation")
#         assert response == "Mocked book recommendation"

#     assert mock_prompt_client.get_prompt_active_version.call_count == num_calls
#     assert mock_create_mirascope_call.call_count == num_calls
#     # Ensure that the function is called at least 5 times in 1 second
