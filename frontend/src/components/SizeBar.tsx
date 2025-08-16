import React from "react";

export default function SizeBar({ bytes }: { bytes: number }) {
  const gb = (bytes / (1024**3)).toFixed(2);
  const mb = (bytes / (1024**2)).toFixed(2);
  return <div>Освободится: {gb} GB ({mb} MB)</div>;
}
