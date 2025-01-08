source ~/.zshrc

# Run the migrations
alembic upgrade head

# Run the FastAPI server
fastapi run
