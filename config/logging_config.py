# logging_config.py
import logging.config
import os

def setup_logging():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,

        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            },
            'file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'standard',
                'filename': os.path.join(log_dir, 'app.log'),
                'maxBytes': 1024 * 1024 * 5,
                'backupCount': 5,
                'encoding': 'utf8'
            },
            'error_file': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'standard',
                'filename': os.path.join(log_dir, 'error.log'),
                'maxBytes': 1024 * 1024 * 5,
                'backupCount': 5,
                'encoding': 'utf8'
            }
        },
        'loggers': {
            # 配置根logger，所有未明确配置的logger都会继承它
            '': {
                'handlers': ['console', 'file', 'error_file'],
                'level': 'INFO',
                'propagate': False # 阻止日志向上级logger传播，避免重复输出
            },
            # Uvicorn的日志，通常由Uvicorn自己管理，但你也可以在这里覆盖
            'uvicorn': {
                'handlers': ['console', 'file'],
                'level': 'WARNING',
                'propagate': False
            },
            'uvicorn.access': {
                'handlers': ['console', 'file'],
                'level': 'WARNING',
                'propagate': False
            },
            # 为你的应用特定模块定义一个logger，可以设置更详细的级别
            'my_app': {
                'handlers': ['console', 'file', 'error_file'],
                'level': 'DEBUG', # 例如，你的应用内部可以打印DEBUG级别日志
                'propagate': False
            }
        },
        'root': { # 根logger的另一种配置方式，与''等效
            'handlers': ['console', 'file'],
            'level': 'INFO'
        }
    }
    logging.config.dictConfig(logging_config)

