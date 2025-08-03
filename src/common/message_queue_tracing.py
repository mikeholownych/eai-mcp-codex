"""
Message queue tracing utilities for RabbitMQ communications.
Provides trace context propagation for message publishing and consumption.
"""

import logging
from typing import Dict, Any, Optional, List, Callable, Union
from contextlib import asynccontextmanager, contextmanager
import asyncio
import json
import time
import uuid

from opentelemetry import trace, context
from opentelemetry.trace import (
    Span, 
    SpanKind, 
    Status, 
    StatusCode,
    set_span_in_context,
    get_current_span,
    get_value_from_span
)
from opentelemetry.propagate import extract, inject
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

import pika
import aio_pika
from aio_pika import Message, ExchangeType
from pika.adapters.utils.connection_workflow import AMQPConnectionWorkflow

from .tracing import get_tracing_config
from .trace_propagation import TracePropagationUtils

logger = logging.getLogger(__name__)

# Global propagator instance
_trace_context_propagator = TraceContextTextMapPropagator()


class MessageQueueTracing:
    """Tracing utilities for RabbitMQ message queue operations."""
    
    def __init__(self):
        self.tracer = get_tracing_config().get_tracer()
        self.propagator = _trace_context_propagator
        self.propagation_utils = TracePropagationUtils()
    
    @asynccontextmanager
    async def trace_message_publish(self, exchange_name: str, routing_key: str, 
                                  message_body: bytes, message_type: str = "default",
                                  correlation_id: str = None):
        """Trace message publishing to RabbitMQ."""
        span_name = "message_queue.publish"
        attributes = {
            "messaging.system": "rabbitmq",
            "messaging.destination": exchange_name,
            "messaging.destination_kind": "exchange",
            "messaging.operation": "publish",
            "messaging.rabbitmq.routing_key": routing_key,
            "messaging.message_type": message_type,
            "messaging.message_payload_size_bytes": len(message_body)
        }
        
        if correlation_id:
            attributes["messaging.conversation_id"] = correlation_id
        
        with self.tracer.start_as_current_span(span_name, kind=SpanKind.PRODUCER, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                span.set_attribute("messaging.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                duration = time.time() - start_time
                span.set_attribute("messaging.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    @asynccontextmanager
    async def trace_message_consume(self, queue_name: str, exchange_name: str, 
                                  consumer_tag: str, message_type: str = "default"):
        """Trace message consumption from RabbitMQ."""
        span_name = "message_queue.consume"
        attributes = {
            "messaging.system": "rabbitmq",
            "messaging.destination": queue_name,
            "messaging.destination_kind": "queue",
            "messaging.operation": "consume",
            "messaging.rabbitmq.exchange_name": exchange_name,
            "messaging.message_type": message_type,
            "messaging.consumer_tag": consumer_tag
        }
        
        with self.tracer.start_as_current_span(span_name, kind=SpanKind.CONSUMER, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                span.set_attribute("messaging.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                duration = time.time() - start_time
                span.set_attribute("messaging.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    @asynccontextmanager
    async def trace_message_processing(self, queue_name: str, message_id: str, 
                                    message_type: str = "default"):
        """Trace message processing after consumption."""
        span_name = "message_queue.process"
        attributes = {
            "messaging.system": "rabbitmq",
            "messaging.destination": queue_name,
            "messaging.destination_kind": "queue",
            "messaging.operation": "process",
            "messaging.message_id": message_id,
            "messaging.message_type": message_type
        }
        
        with self.tracer.start_as_current_span(span_name, kind=SpanKind.SERVER, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                span.set_attribute("messaging.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                duration = time.time() - start_time
                span.set_attribute("messaging.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    @asynccontextmanager
    async def trace_queue_operation(self, operation: str, queue_name: str, 
                                  exchange_name: str = None):
        """Trace queue management operations."""
        span_name = f"message_queue.queue_{operation}"
        attributes = {
            "messaging.system": "rabbitmq",
            "messaging.operation": operation,
            "messaging.destination": queue_name,
            "messaging.destination_kind": "queue"
        }
        
        if exchange_name:
            attributes["messaging.rabbitmq.exchange_name"] = exchange_name
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                span.set_attribute("messaging.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                duration = time.time() - start_time
                span.set_attribute("messaging.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    def inject_trace_context_to_message_headers(self, headers: Dict[str, str] = None) -> Dict[str, str]:
        """Inject trace context into message headers."""
        carrier = headers or {}
        try:
            self.propagator.inject(carrier)
            return carrier
        except Exception as e:
            logger.warning(f"Failed to inject trace context to message headers: {e}")
            return headers or {}
    
    def extract_trace_context_from_message_headers(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Extract trace context from message headers."""
        carrier = headers or {}
        try:
            ctx = self.propagator.extract(carrier)
            return ctx
        except Exception as e:
            logger.warning(f"Failed to extract trace context from message headers: {e}")
            return {}
    
    def create_traced_message(self, body: Union[str, bytes, Dict], 
                            headers: Dict[str, str] = None,
                            message_type: str = "default",
                            correlation_id: str = None,
                            message_id: str = None) -> Dict[str, Any]:
        """Create a message with tracing headers."""
        # Generate message ID if not provided
        if not message_id:
            message_id = str(uuid.uuid4())
        
        # Generate correlation ID if not provided
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Prepare headers
        traced_headers = self.inject_trace_context_to_message_headers(headers or {})
        traced_headers.update({
            "message-id": message_id,
            "message-type": message_type,
            "correlation-id": correlation_id,
            "timestamp": str(int(time.time() * 1000))
        })
        
        # Prepare message body
        if isinstance(body, dict):
            body_bytes = json.dumps(body).encode('utf-8')
        elif isinstance(body, str):
            body_bytes = body.encode('utf-8')
        else:
            body_bytes = body
        
        return {
            "body": body_bytes,
            "headers": traced_headers,
            "message_id": message_id,
            "correlation_id": correlation_id,
            "message_type": message_type
        }
    
    def add_message_attributes_to_span(self, span: Span, message_id: str, 
                                    message_type: str, correlation_id: str,
                                    queue_name: str, exchange_name: str = None):
        """Add message attributes to span."""
        span.set_attribute("messaging.message_id", message_id)
        span.set_attribute("messaging.message_type", message_type)
        span.set_attribute("messaging.conversation_id", correlation_id)
        span.set_attribute("messaging.destination", queue_name)
        
        if exchange_name:
            span.set_attribute("messaging.rabbitmq.exchange_name", exchange_name)
    
    def add_delivery_attributes_to_span(self, span: Span, delivery_tag: int, 
                                      redelivered: bool, exchange: str, 
                                      routing_key: str):
        """Add delivery attributes to span."""
        span.set_attribute("messaging.rabbitmq.delivery_tag", delivery_tag)
        span.set_attribute("messaging.rabbitmq.redelivered", redelivered)
        span.set_attribute("messaging.rabbitmq.exchange", exchange)
        span.set_attribute("messaging.rabbitmq.routing_key", routing_key)


class TracedAioPikaPublisher:
    """Traced aio-pika publisher wrapper."""
    
    def __init__(self, connection: aio_pika.RobustConnection, 
                 message_tracing: MessageQueueTracing):
        self.connection = connection
        self.message_tracing = message_tracing
        self.channel = None
    
    async def __aenter__(self):
        """Enter context manager."""
        self.channel = await self.connection.channel()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self.channel:
            await self.channel.close()
    
    async def publish(self, exchange_name: str, routing_key: str, 
                     body: Union[str, bytes, Dict], headers: Dict[str, str] = None,
                     message_type: str = "default", correlation_id: str = None,
                     persistent: bool = True):
        """Publish a message with tracing."""
        # Create traced message
        traced_message = self.message_tracing.create_traced_message(
            body, headers, message_type, correlation_id
        )
        
        # Create message with tracing
        message = Message(
            body=traced_message["body"],
            headers=traced_message["headers"],
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT if persistent else aio_pika.DeliveryMode.NOT_PERSISTENT
        )
        
        # Get or create exchange
        exchange = await self.channel.get_exchange(exchange_name)
        
        # Trace the publish operation
        async with self.message_tracing.trace_message_publish(
            exchange_name, routing_key, traced_message["body"], 
            message_type, traced_message["correlation_id"]
        ):
            await exchange.publish(message, routing_key=routing_key)
        
        return traced_message["message_id"]
    
    async def declare_exchange(self, exchange_name: str, exchange_type: ExchangeType = ExchangeType.DIRECT):
        """Declare an exchange with tracing."""
        async with self.message_tracing.trace_queue_operation("declare_exchange", exchange_name):
            return await self.channel.declare_exchange(
                exchange_name, 
                exchange_type=exchange_type,
                durable=True
            )
    
    async def declare_queue(self, queue_name: str, durable: bool = True):
        """Declare a queue with tracing."""
        async with self.message_tracing.trace_queue_operation("declare_queue", queue_name):
            return await self.channel.declare_queue(queue_name, durable=durable)
    
    async def bind_queue(self, queue_name: str, exchange_name: str, routing_key: str):
        """Bind a queue to an exchange with tracing."""
        async with self.message_tracing.trace_queue_operation("bind_queue", queue_name, exchange_name):
            queue = await self.channel.declare_queue(queue_name)
            exchange = await self.channel.get_exchange(exchange_name)
            await queue.bind(exchange, routing_key=routing_key)


class TracedAioPikaConsumer:
    """Traced aio-pika consumer wrapper."""
    
    def __init__(self, connection: aio_pika.RobustConnection, 
                 message_tracing: MessageQueueTracing):
        self.connection = connection
        self.message_tracing = message_tracing
        self.channel = None
        self.queue = None
        self.consumer_tag = None
    
    async def __aenter__(self):
        """Enter context manager."""
        self.channel = await self.connection.channel()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self.consumer_tag and self.channel:
            await self.channel.basic_cancel(self.consumer_tag)
        if self.channel:
            await self.channel.close()
    
    async def setup_queue(self, queue_name: str, exchange_name: str = None, 
                         routing_key: str = None, durable: bool = True):
        """Setup queue for consumption with tracing."""
        # Declare queue
        async with self.message_tracing.trace_queue_operation("declare_queue", queue_name):
            self.queue = await self.channel.declare_queue(queue_name, durable=durable)
        
        # Bind to exchange if provided
        if exchange_name and routing_key:
            async with self.message_tracing.trace_queue_operation("bind_queue", queue_name, exchange_name):
                exchange = await self.channel.get_exchange(exchange_name)
                await self.queue.bind(exchange, routing_key=routing_key)
        
        return self.queue
    
    async def consume(self, queue_name: str, callback: Callable, 
                     exchange_name: str = None, auto_ack: bool = False):
        """Start consuming messages with tracing."""
        # Setup queue
        await self.setup_queue(queue_name, exchange_name)
        
        # Create traced callback
        async def traced_callback(message: aio_pika.IncomingMessage):
            # Extract trace context from headers
            headers = dict(message.headers) if message.headers else {}
            ctx = self.message_tracing.extract_trace_context_from_message_headers(headers)
            
            # Get message metadata
            message_id = headers.get("message-id", str(uuid.uuid4()))
            message_type = headers.get("message-type", "default")
            correlation_id = headers.get("correlation-id", str(uuid.uuid4()))
            
            # Trace message consumption
            async with self.message_tracing.trace_message_consume(
                queue_name, exchange_name or "", message.consumer_tag, message_type
            ) as consume_span:
                # Add message attributes to span
                self.message_tracing.add_message_attributes_to_span(
                    consume_span, message_id, message_type, correlation_id, 
                    queue_name, exchange_name
                )
                
                # Add delivery attributes to span
                self.message_tracing.add_delivery_attributes_to_span(
                    consume_span, message.delivery_tag, message.redelivered,
                    message.exchange or "", message.routing_key or ""
                )
                
                # Trace message processing
                async with self.message_tracing.trace_message_processing(
                    queue_name, message_id, message_type
                ) as process_span:
                    try:
                        # Process the message
                        await callback(message)
                        
                        # Acknowledge message if not auto-ack
                        if not auto_ack:
                            await message.ack()
                        
                        process_span.set_status(Status(StatusCode.OK))
                    except Exception as e:
                        # Reject message if not auto-ack
                        if not auto_ack:
                            await message.reject(requeue=False)
                        
                        process_span.set_status(Status(StatusCode.ERROR, str(e)))
                        process_span.record_exception(e)
                        raise
        
        # Start consuming
        self.consumer_tag = await self.queue.consume(traced_callback, auto_ack=auto_ack)
        return self.consumer_tag


class TracedPikaPublisher:
    """Traced pika publisher wrapper for synchronous operations."""
    
    def __init__(self, connection_parameters: pika.ConnectionParameters,
                 message_tracing: MessageQueueTracing):
        self.connection_parameters = connection_parameters
        self.message_tracing = message_tracing
        self.connection = None
        self.channel = None
    
    def __enter__(self):
        """Enter context manager."""
        self.connection = pika.BlockingConnection(self.connection_parameters)
        self.channel = self.connection.channel()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self.channel:
            self.channel.close()
        if self.connection:
            self.connection.close()
    
    def publish(self, exchange_name: str, routing_key: str, 
               body: Union[str, bytes, Dict], headers: Dict[str, str] = None,
               message_type: str = "default", correlation_id: str = None,
               persistent: bool = True):
        """Publish a message with tracing."""
        # Create traced message
        traced_message = self.message_tracing.create_traced_message(
            body, headers, message_type, correlation_id
        )
        
        # Create basic properties
        properties = pika.BasicProperties(
            headers=traced_message["headers"],
            content_type="application/json",
            delivery_mode=2 if persistent else 1  # 2 = persistent, 1 = transient
        )
        
        # Trace the publish operation
        with self.message_tracing.trace_message_publish(
            exchange_name, routing_key, traced_message["body"], 
            message_type, traced_message["correlation_id"]
        ):
            self.channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=traced_message["body"],
                properties=properties
            )
        
        return traced_message["message_id"]
    
    def declare_exchange(self, exchange_name: str, exchange_type: str = "direct"):
        """Declare an exchange with tracing."""
        with self.message_tracing.trace_queue_operation("declare_exchange", exchange_name):
            self.channel.exchange_declare(
                exchange=exchange_name,
                exchange_type=exchange_type,
                durable=True
            )
    
    def declare_queue(self, queue_name: str, durable: bool = True):
        """Declare a queue with tracing."""
        with self.message_tracing.trace_queue_operation("declare_queue", queue_name):
            self.channel.queue_declare(queue=queue_name, durable=durable)
    
    def bind_queue(self, queue_name: str, exchange_name: str, routing_key: str):
        """Bind a queue to an exchange with tracing."""
        with self.message_tracing.trace_queue_operation("bind_queue", queue_name, exchange_name):
            self.channel.queue_bind(
                queue=queue_name,
                exchange=exchange_name,
                routing_key=routing_key
            )


# Decorators for message queue operations
def trace_message_publish(exchange_name: str, routing_key: str, message_type: str = "default"):
    """Decorator to trace message publishing."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            message_tracing = MessageQueueTracing()
            
            # Extract message body from kwargs
            body = kwargs.get('body') or (args[0] if args else b'')
            if isinstance(body, str):
                body = body.encode('utf-8')
            elif isinstance(body, dict):
                body = json.dumps(body).encode('utf-8')
            
            # Extract correlation ID from kwargs
            correlation_id = kwargs.get('correlation_id')
            
            async with message_tracing.trace_message_publish(
                exchange_name, routing_key, body, message_type, correlation_id
            ):
                return await func(*args, **kwargs)
        
        if hasattr(func, '__call__') and hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
            return async_wrapper
        return func
    
    return decorator


def trace_message_consume(queue_name: str, exchange_name: str = None, message_type: str = "default"):
    """Decorator to trace message consumption."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            message_tracing = MessageQueueTracing()
            
            # Extract message from kwargs
            message = kwargs.get('message') or (args[0] if args else None)
            if not message:
                return await func(*args, **kwargs)
            
            # Extract headers from message
            headers = getattr(message, 'headers', {}) or {}
            message_id = headers.get('message-id', str(uuid.uuid4()))
            correlation_id = headers.get('correlation-id', str(uuid.uuid4()))
            consumer_tag = getattr(message, 'consumer_tag', 'unknown')
            
            async with message_tracing.trace_message_consume(
                queue_name, exchange_name or "", consumer_tag, message_type
            ) as consume_span:
                # Add message attributes to span
                message_tracing.add_message_attributes_to_span(
                    consume_span, message_id, message_type, correlation_id, 
                    queue_name, exchange_name
                )
                
                # Trace message processing
                async with message_tracing.trace_message_processing(
                    queue_name, message_id, message_type
                ) as process_span:
                    try:
                        result = await func(*args, **kwargs)
                        process_span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        process_span.set_status(Status(StatusCode.ERROR, str(e)))
                        process_span.record_exception(e)
                        raise
        
        if hasattr(func, '__call__') and hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
            return async_wrapper
        return func
    
    return decorator


# Global instance
message_queue_tracing = MessageQueueTracing()


def get_message_queue_tracing() -> MessageQueueTracing:
    """Get the global message queue tracing instance."""
    return message_queue_tracing


def create_traced_aio_pika_publisher(connection: aio_pika.RobustConnection):
    """Create a traced aio-pika publisher."""
    return TracedAioPikaPublisher(connection, message_queue_tracing)


def create_traced_aio_pika_consumer(connection: aio_pika.RobustConnection):
    """Create a traced aio-pika consumer."""
    return TracedAioPikaConsumer(connection, message_queue_tracing)


def create_traced_pika_publisher(connection_parameters: pika.ConnectionParameters):
    """Create a traced pika publisher."""
    return TracedPikaPublisher(connection_parameters, message_queue_tracing)