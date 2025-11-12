"""
ComicForge 后端入口用于生产/桌面环境。

通过命令行参数控制监听地址和端口，内部启动 uvicorn 服务器。
"""
from __future__ import annotations

import argparse
import contextlib
import signal
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    bundle_dir = Path(getattr(sys, "_MEIPASS"))
    if str(bundle_dir) not in sys.path:
        sys.path.insert(0, str(bundle_dir))

from api.main import app as fastapi_app  # type: ignore  # noqa: E402

try:
    from loguru import logger  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - 打包环境可能缺失 loguru
    import logging

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    logger = logging.getLogger("comicforge")


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="启动 ComicForge FastAPI 后端服务",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="监听地址（默认：127.0.0.1）",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7864,
        help="监听端口（默认：7864）",
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="日志级别（默认：info）",
    )
    parser.add_argument(
        "--app-dir",
        default=None,
        help="FastAPI 应用目录（默认：src）",
    )
    return parser


def configure_logging(log_level: str) -> None:
    level = log_level.upper()
    if hasattr(logger, "remove"):
        logger.remove()
        logger.add(sys.stdout, level=level)
    else:
        logger.setLevel(level)


def run_server(host: str, port: int, log_level: str, app_dir: Path | None) -> int:
    try:
        import uvicorn
    except ModuleNotFoundError:  # pragma: no cover - 运行时才可能发生
        logger.error("未安装 uvicorn，请先安装依赖。")
        return 1

    kwargs = {"host": host, "port": port, "log_level": log_level}

    logger.info(f"启动 ComicForge 后端：{host}:{port}（日志级别：{log_level}）")

    server = uvicorn.Server(uvicorn.Config(fastapi_app, **kwargs))

    # 优雅退出
    stop_signals = (signal.SIGINT, signal.SIGTERM)
    for sig in stop_signals:
        with contextlib.suppress(ValueError):
            signal.signal(sig, server.handle_exit)

    return 0 if server.run() else 1


def main() -> int:
    parser = create_argument_parser()
    args = parser.parse_args()

    app_dir = Path(args.app_dir).resolve() if args.app_dir else ROOT_DIR

    configure_logging(args.log_level)
    return run_server(args.host, args.port, args.log_level, app_dir)


if __name__ == "__main__":
    sys.exit(main())


