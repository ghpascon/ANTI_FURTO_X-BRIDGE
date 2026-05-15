import asyncio
import importlib
import inspect
import logging
import os
import sys

from smartx_rfid.utils.path import get_frozen_path


async def restartable_task(func, *args, **kwargs):
	"""Executa uma coroutine que se reinicia automaticamente em caso de erro."""
	name = f'{func.__module__}.{func.__name__}'

	while True:
		try:
			logging.info(f'🚀 Starting task {name}')
			await func(*args, **kwargs)
			logging.warning(f'🛑 Task {name} finished normally — not restarting')
			break

		except asyncio.CancelledError:
			logging.warning(f'⚠️ Task {name} cancelled — exiting cleanly')
			break

		except KeyboardInterrupt:
			logging.warning(f'🧹 Task {name} received KeyboardInterrupt — exiting program')
			raise  # Propaga o Ctrl+C para encerrar o programa

		except Exception as e:
			logging.exception(f'💥 Task {name} crashed: {e}. Restarting in 1s...')
			await asyncio.sleep(1)


async def create_async_tasks(module_dir):
	"""Create restartable async tasks from coroutine functions in the specified directory."""
	package_path = os.path.abspath(get_frozen_path(module_dir))
	sys.path.insert(0, os.path.dirname(package_path))
	package_name = os.path.basename(package_path)

	tasks = []

	for file in os.listdir(module_dir):
		full_path = os.path.join(module_dir, file)

		if file == '__pycache__':
			continue

		if os.path.isdir(full_path) and not file.startswith('.'):
			sub_tasks = await create_async_tasks(full_path)
			tasks.extend(sub_tasks)

		elif file.endswith('.py') and file != '__init__.py':
			module_name = f'{package_name}.{file[:-3]}'
			module = importlib.import_module(module_name)

			for name, func in inspect.getmembers(module, inspect.iscoroutinefunction):
				if func.__module__ == module.__name__:
					task = asyncio.create_task(restartable_task(func))
					tasks.append(task)
					logging.info(f'✅ Registered restartable task {file} - {name}()')

	return tasks
