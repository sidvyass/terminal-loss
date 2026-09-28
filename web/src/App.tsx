import { Footer, Nav, StatusStrip } from "./Chrome";
import { Countries } from "./countries/Countries";
import { Markets } from "./markets/Markets";
import { useDashboard } from "./useDashboard";

export function App() {
  const d = useDashboard();
  const { snapshot } = d;
  return (
    <div className="app">
      <Nav d={d} />
      <StatusStrip d={d} />
      {!snapshot ? (
        <section className="section loading">
          {d.error && !d.refreshing
            ? `Could not reach the API (${d.error}). Is market-api running? Retrying on the next refresh.`
            : "Fetching quotes and country data… (the first run takes about 15s)"}
        </section>
      ) : d.tab === "markets" ? (
        <Markets d={d} quotes={snapshot.quotes} extras={snapshot.extras} />
      ) : (
        <Countries d={d} countries={snapshot.countries} />
      )}
      <Footer tab={d.tab} />
    </div>
  );
}
