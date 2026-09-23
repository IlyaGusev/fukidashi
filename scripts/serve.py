import fire
import uvicorn


def main(port: int = 8083, host: str = "127.0.0.1", reload: bool = False) -> None:
    uvicorn.run("panelogue.web:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    fire.Fire(main)
