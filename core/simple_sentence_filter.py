from pipecat.frames.frames import TextFrame, Frame
from pipecat.processors.filters.function_filter import FunctionFilter
from pipecat.processors.frame_processor import FrameDirection
import re
import hashlib
import time
from typing import Set, Optional


class SimpleSentenceDuplicateFilter:
    """
    Simple filter that only blocks complete duplicate sentences,
    allowing individual words/chunks to pass through normally.
    """

    def __init__(self):
        self.complete_sentences: Set[str] = set()
        self.current_accumulation = ""
        self.last_chunk_time = 0
        self.accumulation_timeout = 2.0  # Reset accumulation after 2 seconds

    def _normalize_sentence(self, text: str) -> str:
        """Normalize sentence for comparison"""
        # Remove extra whitespace and punctuation, convert to lowercase
        normalized = re.sub(r"\s+", " ", text.lower().strip())
        normalized = re.sub(r"[^\w\s]", "", normalized)
        return normalized

    def _create_sentence_hash(self, text: str) -> str:
        """Create hash of normalized sentence"""
        normalized = self._normalize_sentence(text)
        return hashlib.md5(normalized.encode()).hexdigest()

    def _is_sentence_boundary(self, text: str) -> bool:
        """Check if text represents end of sentence"""
        text = text.strip()
        # Look for sentence ending punctuation or long pauses
        return (
            text.endswith(".")
            or text.endswith("?")
            or text.endswith("!")
            or
            # If accumulation is getting long, treat as sentence
            len(self.current_accumulation + " " + text) > 80
        )

    def _should_reset_accumulation(self) -> bool:
        """Check if we should reset sentence accumulation"""
        current_time = time.time()
        return (current_time - self.last_chunk_time) > self.accumulation_timeout

    async def filter_function(self, frame: Frame) -> bool:
        """
        Filter function that only blocks complete duplicate sentences
        """
        if not isinstance(frame, TextFrame):
            return True

        text = frame.text.strip()
        current_time = time.time()

        # Always allow very short chunks
        if len(text) < 2:
            return True

        # Reset accumulation if too much time has passed
        if self._should_reset_accumulation():
            self.current_accumulation = ""

        # Add current text to accumulation
        if self.current_accumulation:
            self.current_accumulation += " " + text
        else:
            self.current_accumulation = text

        self.last_chunk_time = current_time

        # Check if this completes a sentence
        if self._is_sentence_boundary(text):
            complete_sentence = self.current_accumulation.strip()
            sentence_hash = self._create_sentence_hash(complete_sentence)

            # Check for duplicate complete sentence
            if sentence_hash in self.complete_sentences:
                print(
                    f"[SIMPLE-FILTER] Blocked duplicate sentence: '{complete_sentence}'"
                )
                # Reset accumulation but block this chunk
                self.current_accumulation = ""
                return False

            # Store the sentence hash and allow
            self.complete_sentences.add(sentence_hash)
            print(f"[SIMPLE-FILTER] Allowed new sentence: '{complete_sentence}'")

            # Reset accumulation for next sentence
            self.current_accumulation = ""

        # Allow individual chunks to pass through
        return True


def create_simple_sentence_filter() -> FunctionFilter:
    """
    Create a simple sentence-level duplicate filter

    This filter only blocks complete duplicate sentences, allowing
    individual word chunks to pass through normally.
    """
    sentence_filter = SimpleSentenceDuplicateFilter()

    return FunctionFilter(
        filter=sentence_filter.filter_function, direction=FrameDirection.DOWNSTREAM
    )


# Usage example
if __name__ == "__main__":
    # Test the filters
    test_chunks = [
        "Good morning",
        "Shafiq.",
        "I am Lucy,",
        "your general practice",
        "assistant.",
        "How can I help you?",
        # Duplicate attempt
        "Good morning",
        "Shafiq.",
        "I am Lucy,",
        "your general practice",
        "assistant.",
        "How can I help you?",
    ]

    # Test simple sentence filter
    sentence_filter = SimpleSentenceDuplicateFilter()
    print("Testing Simple Sentence Filter:")
    for chunk in test_chunks:

        class MockFrame:
            def __init__(self, text):
                self.text = text

        frame = MockFrame(chunk)
        result = sentence_filter.filter_function(frame)
        print(f"  '{chunk}' -> {'ALLOWED' if result else 'BLOCKED'}")

    print("\n" + "=" * 50 + "\n")
