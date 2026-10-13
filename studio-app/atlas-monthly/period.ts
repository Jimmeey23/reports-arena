export const monthLabel = (month: string) =>
  new Date(month + "-01T00:00:00Z").toLocaleDateString("en-GB", {
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  });
/** "Aug '25" for chart axes. */
export const monthShort = (month: string) => {
  const d = new Date(month + "-01T00:00:00Z");
  return `${d.toLocaleDateString("en-GB", { month: "short", timeZone: "UTC" })} '${String(d.getUTCFullYear()).slice(2)}`;
};