# capstone-team4
Medical Cache Inventory Management in Remote and Austere Environments

## Encrypted inventory metadata

Uploads store `lot_number` and `location` together as Fernet-encrypted metadata
in the SQLAlchemy inventory table; those values are not included in API responses.
The app migrates an existing `inventory_items` table when it starts.

Set `INVENTORY_ENCRYPTION_KEY` to a Fernet key for deployments. If it is unset,
the app creates and reuses a local `secret.key` file. Keep that key backed up and
private: encrypted metadata cannot be recovered without the same key.
