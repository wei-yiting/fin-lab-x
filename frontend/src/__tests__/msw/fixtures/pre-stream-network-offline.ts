import type { NetworkFailureFixture } from "./types";

const fixture: NetworkFailureFixture = {
  description: "Simulated fetch TypeError — network offline",
  scenarios: ["S-err-01 (row 5: network offline)", "S-err-09 base"],
  networkFailure: true,
};

export default fixture;
