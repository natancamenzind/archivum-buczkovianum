import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AudioPlayer } from "@/components/AudioPlayer";
import { axeViolations } from "@/test/render";

const SRC = "https://archive.org/download/buczkowski-wywiad-1975/strona-a.mp3";
const DURATION = 754; // 12:34

/** The audio element; jsdom plays nothing, so the tests fire its media events themselves. */
function audioElement(container: HTMLElement): HTMLAudioElement {
  const audio = container.querySelector("audio");
  if (audio === null) {
    throw new Error("The player has no audio element.");
  }
  Object.defineProperty(audio, "currentTime", { value: 0, writable: true });
  return audio;
}

function loadMetadata(audio: HTMLAudioElement) {
  Object.defineProperty(audio, "duration", { value: DURATION });
  fireEvent(audio, new Event("loadedmetadata"));
}

function renderLoaded() {
  const { container } = render(<AudioPlayer src={SRC} />);
  const audio = audioElement(container);
  loadMetadata(audio);
  return { container, audio };
}

describe("AudioPlayer", () => {
  const play = vi.spyOn(HTMLMediaElement.prototype, "play");
  const pause = vi.spyOn(HTMLMediaElement.prototype, "pause");

  beforeEach(() => {
    play.mockResolvedValue(undefined);
    pause.mockReturnValue(undefined);
    // jsdom has no pointer capture.
    HTMLElement.prototype.setPointerCapture = () => undefined;
  });

  afterEach(() => {
    play.mockReset();
    pause.mockReset();
  });

  it("ARC-58: plays the linked file in the browser's audio element, not a provider's player", async () => {
    const { container } = render(<AudioPlayer src={SRC} />);

    expect(audioElement(container)).toHaveAttribute("src", SRC);
    expect(screen.getByRole("group", { name: "Odtwarzacz nagrania" })).toBeVisible();
    expect(container.querySelector("iframe")).not.toBeInTheDocument();
    expect(await axeViolations(container)).toEqual([]);
  });

  it("ARC-58: shows no times and a disabled slider until the recording's length is known", () => {
    render(<AudioPlayer src={SRC} />);

    expect(screen.getAllByText("--:--")).toHaveLength(2);
    expect(screen.getByRole("slider", { name: "Postęp nagrania" })).toHaveAttribute(
      "aria-disabled",
      "true",
    );
  });

  it("ARC-58: shows the elapsed and total time once the length is known", async () => {
    const { container } = renderLoaded();

    expect(screen.getByText("00:00")).toBeVisible();
    expect(screen.getByText("12:34")).toBeVisible();
    const slider = screen.getByRole("slider", { name: "Postęp nagrania" });
    expect(slider).toHaveAttribute("aria-disabled", "false");
    expect(slider).toHaveAttribute("aria-valuemax", "754");
    expect(await axeViolations(container)).toEqual([]);
  });

  it("ARC-58: play starts the recording and the button turns into pause", () => {
    const { audio } = renderLoaded();

    fireEvent.click(screen.getByRole("button", { name: "Odtwórz" }));
    expect(play).toHaveBeenCalled();

    fireEvent(audio, new Event("play"));
    Object.defineProperty(audio, "paused", { value: false });
    fireEvent.click(screen.getByRole("button", { name: "Wstrzymaj" }));
    expect(pause).toHaveBeenCalled();

    fireEvent(audio, new Event("pause"));
    expect(screen.getByRole("button", { name: "Odtwórz" })).toBeVisible();
  });

  it("ARC-58: the elapsed time and the slider follow playback", () => {
    const { audio } = renderLoaded();

    audio.currentTime = 135;
    fireEvent(audio, new Event("timeupdate"));

    expect(screen.getByText("02:15")).toBeVisible();
    expect(screen.getByRole("slider")).toHaveAttribute(
      "aria-valuetext",
      "2 min 15 s z 12 min 34 s",
    );
  });

  it("ARC-58: dragging the slider shows the target time and jumps there on release", () => {
    const { audio } = renderLoaded();
    const slider = screen.getByRole("slider");
    vi.spyOn(slider, "getBoundingClientRect").mockReturnValue(new DOMRect(100, 0, 400, 16));

    fireEvent.pointerDown(slider, { clientX: 200, pointerId: 1 });
    fireEvent.pointerMove(slider, { clientX: 300, pointerId: 1 });

    const target = screen.getByText("06:17");
    expect(target).toHaveClass("text-accent-foreground");
    expect(audio.currentTime).toBe(0);

    fireEvent.pointerUp(slider, { clientX: 300, pointerId: 1 });

    expect(audio.currentTime).toBe(377);
    expect(screen.getByText("06:17")).toHaveClass("text-foreground");
  });

  it("ARC-58: the slider's arrow keys move 5 seconds, Home and End to either end", () => {
    const { audio } = renderLoaded();
    const slider = screen.getByRole("slider");

    fireEvent.keyDown(slider, { key: "ArrowRight" });
    expect(audio.currentTime).toBe(5);
    fireEvent.keyDown(slider, { key: "ArrowLeft" });
    fireEvent.keyDown(slider, { key: "ArrowLeft" });
    expect(audio.currentTime).toBe(0);
    fireEvent.keyDown(slider, { key: "End" });
    expect(audio.currentTime).toBe(DURATION);
    fireEvent.keyDown(slider, { key: "Home" });
    expect(audio.currentTime).toBe(0);
  });

  it("ARC-58: a link that does not play shows a message and a link to the recording", async () => {
    const { container } = render(<AudioPlayer src="https://example.com/nagranie" />);

    fireEvent(audioElement(container), new Event("error"));

    expect(screen.getByText("Nie udało się wczytać nagrania.")).toBeVisible();
    const link = screen.getByRole("link", { name: "Otwórz nagranie" });
    expect(link).toHaveAttribute("href", "https://example.com/nagranie");
    expect(link).toHaveAttribute("target", "_blank");
    expect(screen.queryByRole("slider")).not.toBeInTheDocument();
    expect(await axeViolations(container)).toEqual([]);
  });
});
