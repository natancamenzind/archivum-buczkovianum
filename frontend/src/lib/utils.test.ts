import { describe, expect, it } from "vitest";

import { cn } from "./utils";

describe("cn", () => {
  it("joins class names and drops falsy ones", () => {
    expect(cn("bg-background", false, null, undefined, "p-16")).toBe("bg-background p-16");
  });

  it("lets a later token class override a conflicting one", () => {
    expect(cn("bg-background p-16", "bg-card p-page")).toBe("bg-card p-page");
    expect(cn("shadow-card", "shadow-raised")).toBe("shadow-raised");
  });

  it("keeps a text colour next to a typography style", () => {
    expect(cn("text-muted-foreground", "text-cousine-etykieta")).toBe(
      "text-muted-foreground text-cousine-etykieta",
    );
  });

  it("keeps a responsive typography style next to the base one", () => {
    expect(cn("text-lora-tytul-strony-mobile", "md:text-lora-tytul-strony")).toBe(
      "text-lora-tytul-strony-mobile md:text-lora-tytul-strony",
    );
  });

  it("lets a later typography style override an earlier one", () => {
    expect(cn("text-lora-tekst", "text-cousine-metadane")).toBe("text-cousine-metadane");
    expect(cn("text-chmura-tagow-1", "text-chmura-tagow-5")).toBe("text-chmura-tagow-5");
  });
});
