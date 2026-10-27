import { setupServer } from "msw/node";

/** Mocks the API at the network level (AGENTS.md). Tests add handlers with `server.use()`. */
export const server = setupServer();
