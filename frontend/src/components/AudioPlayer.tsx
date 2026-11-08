import { useRef, useState, type KeyboardEvent, type PointerEvent } from "react";

import { ArrowUpRightIcon, LoadingIcon, PauseIcon, PlayIcon } from "@/components/icons";
import { copy } from "@/copy/pl";
import { cn } from "@/lib/utils";

/** How far the slider's arrow keys move, in seconds. */
const KEY_STEP = 5;

const FRAME = "rounded-md border border-border bg-muted px-16 py-12";

/** "02:15", or "1:02:15" past an hour. */
function clock(seconds: number): string {
  const whole = Math.floor(seconds);
  const minutes = String(Math.floor((whole % 3600) / 60)).padStart(2, "0");
  const rest = `${minutes}:${String(whole % 60).padStart(2, "0")}`;
  return whole >= 3600 ? `${String(Math.floor(whole / 3600))}:${rest}` : rest;
}

const clamp = (value: number, max: number) => Math.min(Math.max(value, 0), max);

/**
 * "Odtwarzacz audio" in design/components/ (ARC-58): the browser's audio element behind the
 * design's controls: play/pause, a slider to click or drag, the elapsed and total time. A source
 * that cannot be played turns it into a message with a link to the recording.
 */
export function AudioPlayer({ src }: { src: string }) {
  const audio = useRef<HTMLAudioElement>(null);
  const [duration, setDuration] = useState<number | null>(null);
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [buffering, setBuffering] = useState(false);
  const [failed, setFailed] = useState(false);
  // Where the slider is being dragged to; the recording jumps there on release.
  const [scrub, setScrub] = useState<number | null>(null);

  if (failed) {
    return (
      <div
        className={cn(
          FRAME,
          "flex flex-col gap-4 md:flex-row md:items-center md:justify-between md:gap-12",
        )}
      >
        <p className="text-cousine-metadane text-muted-foreground">{copy.audio.error}</p>
        <a
          href={src}
          target="_blank"
          rel="noreferrer"
          className="flex w-fit items-center gap-4 text-cousine-metadane text-accent-foreground underline-offset-3 hover:text-accent-foreground-hover hover:underline focus-visible:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        >
          {copy.content.link}
          <ArrowUpRightIcon className="size-16" />
        </a>
      </div>
    );
  }

  const loaded = duration !== null;
  const shown = scrub ?? time;
  const share = loaded && duration > 0 ? clamp(shown / duration, 1) : 0;

  function seek(to: number) {
    const element = audio.current;
    if (element === null || duration === null) {
      return;
    }
    const target = clamp(to, duration);
    element.currentTime = target;
    setTime(target);
  }

  function toggle() {
    const element = audio.current;
    if (element === null) {
      return;
    }
    if (element.paused) {
      // A source that cannot be played also fires `error`, which shows the message.
      element.play().catch(() => undefined);
    } else {
      element.pause();
    }
  }

  function pointerTime(event: PointerEvent<HTMLDivElement>): number {
    const box = event.currentTarget.getBoundingClientRect();
    return box.width > 0 ? clamp((event.clientX - box.left) / box.width, 1) * (duration ?? 0) : 0;
  }

  function onPointerDown(event: PointerEvent<HTMLDivElement>) {
    if (!loaded) {
      return;
    }
    event.currentTarget.setPointerCapture(event.pointerId);
    setScrub(pointerTime(event));
  }

  function onPointerMove(event: PointerEvent<HTMLDivElement>) {
    if (scrub !== null) {
      setScrub(pointerTime(event));
    }
  }

  function onPointerUp(event: PointerEvent<HTMLDivElement>) {
    if (scrub !== null) {
      seek(pointerTime(event));
      setScrub(null);
    }
  }

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    const targets: Record<string, number> = {
      ArrowLeft: time - KEY_STEP,
      ArrowDown: time - KEY_STEP,
      ArrowRight: time + KEY_STEP,
      ArrowUp: time + KEY_STEP,
      Home: 0,
      End: duration ?? 0,
    };
    const target = targets[event.key];
    if (target !== undefined) {
      event.preventDefault();
      seek(target);
    }
  }

  const Icon = !loaded || buffering ? LoadingIcon : playing ? PauseIcon : PlayIcon;

  return (
    <div
      role="group"
      aria-label={copy.content.player}
      className={cn(FRAME, "flex items-center gap-8 md:gap-12")}
    >
      <audio
        ref={audio}
        src={src}
        preload="metadata"
        onLoadedMetadata={(event) => {
          const length = event.currentTarget.duration;
          setDuration(Number.isFinite(length) ? length : 0);
        }}
        onTimeUpdate={(event) => {
          setTime(event.currentTarget.currentTime);
        }}
        onPlay={() => {
          setPlaying(true);
        }}
        onPause={() => {
          setPlaying(false);
        }}
        onWaiting={() => {
          setBuffering(true);
        }}
        onPlaying={() => {
          setBuffering(false);
        }}
        onError={() => {
          setFailed(true);
        }}
      />
      {/* 40 px like the design; `after:` widens the touch target to 48 px. */}
      <button
        type="button"
        onClick={toggle}
        aria-label={playing ? copy.audio.pause : copy.audio.play}
        className="relative shrink-0 rounded-full bg-primary p-12 text-inverse-icon transition-colors duration-150 ease-out after:absolute after:-inset-4 hover:bg-primary-hover focus-visible:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring motion-reduce:transition-none"
      >
        <Icon
          className={cn(
            "size-16",
            Icon === LoadingIcon && "animate-spin motion-reduce:animate-none",
          )}
        />
      </button>
      <span
        className={cn(
          "text-cousine-metadane",
          scrub === null ? "text-foreground" : "text-accent-foreground",
        )}
      >
        {loaded ? clock(shown) : copy.audio.unknownTime}
      </span>
      <div
        role="slider"
        tabIndex={loaded ? 0 : -1}
        aria-label={copy.audio.progress}
        aria-valuemin={0}
        aria-valuemax={Math.floor(duration ?? 0)}
        aria-valuenow={Math.floor(shown)}
        aria-valuetext={copy.audio.position(shown, duration ?? 0)}
        aria-disabled={!loaded}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={() => {
          setScrub(null);
        }}
        onKeyDown={onKeyDown}
        className={cn(
          "group flex h-24 min-w-0 flex-1 touch-none items-center md:h-16 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
          loaded ? "cursor-pointer" : "opacity-40",
        )}
      >
        {/* Postęp, Uchwyt, Reszta: the grow ratio splits the track around the handle. */}
        <span className="h-4 rounded-full bg-primary" style={{ flexGrow: share }} />
        {loaded && (
          <span
            data-scrubbing={scrub !== null}
            className="size-12 shrink-0 rounded-full bg-primary ring-accent transition-all duration-150 ease-out group-hover:size-16 group-hover:ring-4 group-focus-visible:size-16 group-focus-visible:ring-4 data-[scrubbing=true]:size-16 data-[scrubbing=true]:ring-4 motion-reduce:transition-none"
          />
        )}
        <span className="h-4 rounded-full bg-media" style={{ flexGrow: 1 - share }} />
      </div>
      <span className="text-cousine-metadane text-muted-foreground">
        {loaded && duration > 0 ? clock(duration) : copy.audio.unknownTime}
      </span>
    </div>
  );
}
