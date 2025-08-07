#!/bin/bash
if [ -d "database/migrations" ]; then
  cp -r database/migrations ./migrations
fi
if [ -f "database/migrations/alembic.ini" ]; then
  cp database/migrations/alembic.ini ./alembic.ini
fi
