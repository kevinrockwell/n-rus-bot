"""Scheduler implementation for NRus"""
import asyncio
from datetime import timedelta

from motor.motor_asyncio import AsyncIOMotorCollection


class Scheduler:
    SAMPLE_INTERVAL = timedelta(hours=1)

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection: AsyncIOMotorCollection = collection
        self.tasks = asyncio.queues.Queue()
        # TODO Schedule existing tasks
