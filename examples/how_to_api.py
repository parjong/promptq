"""How to use the promptq Python API: enqueue a prompt, claim it, and remove it.

The queue lives wherever PROMPTQ_HOME points, so run this against a throwaway directory:

    PROMPTQ_HOME="$(mktemp -d)/queue" uv run python examples/how_to_api.py
"""

from promptq import Enqueued, Queue, Selector


def main() -> None:
    queue = Queue()  # constructing does not read or create anything

    # Producer: add a prompt. on_dup is required so what happens to a duplicate is always visible.
    result = queue.enqueue("myapp/TRANSLATE/2", "Translate this page.", on_dup="ignore")
    assert isinstance(result, Enqueued)
    print(f"enqueued {result.name}")

    # Consumer: take the oldest matching prompt. None means there is nothing to claim.
    claimed = queue.claim_one(Selector.prefix("myapp/"))
    assert claimed is not None
    print(f"claimed {claimed.name}: {claimed.body}")

    # When the work is done, remove the prompt. False would mean it was no longer claimed.
    assert queue.dequeue(claimed.name)
    print("done")


if __name__ == "__main__":
    main()
