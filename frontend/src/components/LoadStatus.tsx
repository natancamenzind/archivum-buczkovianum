import { Hypocycloid } from "@/components/Hypocycloid";
import { cn } from "@/lib/utils";

/**
 * The status line of data that is not there yet: `loading` while it loads, `error` once it fails.
 * It grows to fill its flex column, and when the data fails the hypocycloid of the not-found page
 * fills that free space behind the message (ARC-63).
 */
export function LoadStatus({
  pending,
  loading,
  error,
  className,
}: {
  pending: boolean;
  loading: string;
  error: string;
  className?: string;
}) {
  return (
    <div className={cn("relative flex-1 overflow-hidden", className)}>
      {!pending && <Hypocycloid tone="page" placement="notFound" />}
      <p className="relative text-cousine-metadane text-muted-foreground" role="status">
        {pending ? loading : error}
      </p>
    </div>
  );
}
