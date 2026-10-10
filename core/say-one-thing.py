import argparse
import asyncio
import os

from dotenv import load_dotenv
from loguru import logger

from pipecat.frames.frames import EndFrame, TTSSpeakFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketParams, FastAPIWebsocketTransport
from pipecat.transports.services.daily import DailyParams, DailyTransport


if os.getenv('ENVIRONMENT') != 'production':
    load_dotenv(override=True)


async def create_transport(transport_type: str):
    """Create the appropriate transport based on type"""
    if transport_type == "daily":
        # Token is optional - can be None for public rooms
        token = os.environ.get("DAILY_TOKEN") if os.environ.get("DAILY_TOKEN") else None
        return DailyTransport(
            room_url=os.environ.get("DAILY_ROOM_URL"),
            token=token,
            bot_name="Voice Bot",
            params=DailyParams(audio_out_enabled=True, audio_in_enabled=True)
        )
    elif transport_type == "twilio":
        return FastAPIWebsocketTransport(
            params=FastAPIWebsocketParams(audio_out_enabled=True)
        )
    else:
        # For webrtc or other transports, you'll need to implement these
        raise ValueError(f"Transport {transport_type} not implemented yet")


async def run_bot(transport_type: str):
    logger.info(f"Starting bot with {transport_type} transport")

    # Create transport
    transport = await create_transport(transport_type)

    # Create TTS service
    tts = CartesiaTTSService(
        api_key=os.environ.get("CARTESIA_API_KEY"),
        voice_id=os.environ.get("CARTESIA_VOICE_ID"),  # British Reading Lady
    )

    # Create pipeline
    pipeline = Pipeline([tts, transport.output()])
    task = PipelineTask(pipeline)
    
    # Create and run the pipeline runner
    runner = PipelineRunner()
    
    # Register event handler BEFORE running the pipeline
    @transport.event_handler("on_participant_joined")
    async def on_participant_joined(transport, participant):
        logger.info(f"Participant joined: {participant}")
        # Give a small delay to ensure audio connection is ready
        await asyncio.sleep(1)
        await task.queue_frames([
            TTSSpeakFrame("Good morning, you've reached Westfield Medical Centre reception. This is Sarah, um, what can I help you with today?"),
            
            # EndFrame()
        ])
    
    # Also handle when the bot itself joins
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Bot connected to room")
        # Optional: Play a greeting when bot connects
        await task.queue_frames([
        #     TTSSpeakFrame("Voice bot is now online."), 
            TTSSpeakFrame("Sorry guys, I'm running behind this morning - really apologize. Traffic was mental and then I couldn't get the link to work properly. Um, what are we covering first?"), 
        #     EndFrame()
        ])
    
    # Handle when participants leave
    @transport.event_handler("on_participant_left")
    async def on_participant_left(transport, participant, reason):
        logger.info(f"Participant left: {participant}, reason: {reason}")
    
    try:
        await runner.run(task)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        await transport.cleanup()


async def main():
    parser = argparse.ArgumentParser(description="Voice Bot")
    parser.add_argument(
        "--transport", 
        choices=["daily", "twilio", "webrtc"], 
        default="daily",
        help="Transport to use"
    )
    
    args = parser.parse_args()
    
    # Check required environment variables
    required_vars = ["CARTESIA_API_KEY", "CARTESIA_VOICE_ID"]
    if args.transport == "daily":
        required_vars.extend(["DAILY_ROOM_URL"])  # DAILY_TOKEN is optional
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return
    
    await run_bot(args.transport)


if __name__ == "__main__":
    asyncio.run(main())