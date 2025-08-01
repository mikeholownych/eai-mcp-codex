import fs from 'fs';
import { run } from '../src/commands/batch';

// Mock AgentClient to avoid loading its heavy dependencies
jest.mock('../src/commands/agent', () => {
  return {
    AgentClient: jest.fn().mockImplementation(() => ({
      dispatchCommand: jest.fn(),
    })),
  };
});

// Import after mocking so the mocked version is used
import { AgentClient } from '../src/commands/agent';

describe('batch command', () => {
  const tempFile = 'temp-batch.json';

  beforeEach(() => {
    (AgentClient as jest.Mock).mockClear();
  });

  afterEach(() => {
    if (fs.existsSync(tempFile)) {
      fs.unlinkSync(tempFile);
    }
  });

  it('executes commands from JSON file', async () => {
    const mockDispatch = jest.fn();
    (AgentClient as unknown as jest.Mock).mockImplementation(() => ({
      dispatchCommand: mockDispatch,
    }));

    fs.writeFileSync(tempFile, JSON.stringify([{ command: 'plan', args: { task: 'test' } }]));

    await run(tempFile, {});

    expect(mockDispatch).toHaveBeenCalledWith('plan', { task: 'test' });
  });
});
