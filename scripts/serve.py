import fire
import uvicorn

from fukidashi.settings import settings


def main(port: int = settings.port, host: str = settings.host, reload: bool = False) -> None:
    uvicorn.run("fukidashi.web:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    fire.Fire(main)
