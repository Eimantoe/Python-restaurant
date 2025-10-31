# kitchen-common/README.md
# Kitchen Common

Shared models, events, and utilities for Kitchen microservices.

## Installation

### From local directory (development)
```bash
pip install -e /path/to/kitchen-common
```

## Usage
```python
from kitchen_common.events import OrderPlaced
from kitchen_common.models.inventory import Menu
from kitchen_common.shared import logger, redis_service

# Use events
order = OrderPlaced(
    order_id=1,
    table_no=5,
    items=[{"pizza": 2}],
    comments="Extra cheese"
)

# Use models
menu = Menu(items=[])

# Use shared services
logger.info("Order placed", order_id=order.order_id)
```

## Components

- **events**: Event schemas (OrderPlaced, OrderReady, OrderCanceled)
- **models**: Pydantic models for inventory and waitress services
- **shared**: Redis, HTTP client, logging, settings utilities