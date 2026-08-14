/**
 * Avatar component — shows user initials with a deterministic colour,
 * or falls back to an image URL if provided.
 */

"use client";

import { getInitials, getAvatarColor } from "@/lib/utils";

interface AvatarProps {
  name: string;
  src?: string | null;
  size?: number;
  className?: string;
}

export default function Avatar({
  name,
  src,
  size = 40,
  className = "",
}: AvatarProps) {
  if (src) {
    return (
      <img
        src={src}
        alt={name}
        width={size}
        height={size}
        className={`rounded-full object-cover flex-shrink-0 ${className}`}
        style={{ width: size, height: size }}
      />
    );
  }

  return (
    <div
      className={`rounded-full flex items-center justify-center flex-shrink-0 font-semibold select-none ${className}`}
      style={{
        width: size,
        height: size,
        backgroundColor: getAvatarColor(name),
        color: "#fff",
        fontSize: size * 0.35,
      }}
      aria-label={name}
    >
      {getInitials(name)}
    </div>
  );
}
