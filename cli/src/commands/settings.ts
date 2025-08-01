import { Command } from 'commander';
import { ConfigurationManager } from '../config/configuration-manager';

export const settingsCommand = new Command('settings')
  .description('Display resolved settings')
  .action(async () => {
    const configManager = new ConfigurationManager();
    const hierarchy = await configManager.loadConfigurations();
    console.log(JSON.stringify(hierarchy.settings, null, 2));
  });
