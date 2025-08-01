#!/usr/bin/env node

/**
 * Simple test script to validate the MCP configuration system
 * Run with: node examples/test-configuration.js
 */

const path = require('path');
const fs = require('fs');

// Test configuration system by importing and testing core components
async function testConfigurationSystem() {
  console.log('🧪 Testing MCP Configuration System\n');

  try {
    // Test 1: Check if example configurations exist
    console.log('1. Checking example configuration files...');
    
    const exampleAgentPath = path.join(__dirname, 'configurations/example-planner-agent.md');
    const exampleCommandPath = path.join(__dirname, 'configurations/commands/example-generate-command.md');
    
    if (fs.existsSync(exampleAgentPath)) {
      console.log('   ✅ Example agent configuration found');
    } else {
      console.log('   ❌ Example agent configuration missing');
    }
    
    if (fs.existsSync(exampleCommandPath)) {
      console.log('   ✅ Example command configuration found');
    } else {
      console.log('   ❌ Example command configuration missing');
    }

    // Test 2: Validate YAML front matter parsing
    console.log('\n2. Testing YAML front matter parsing...');
    
    const agentContent = fs.readFileSync(exampleAgentPath, 'utf8');
    const frontMatterMatch = agentContent.match(/^---\s*\n([\s\S]*?)\n---\s*\n/);
    
    if (frontMatterMatch) {
      console.log('   ✅ Front matter detected in agent configuration');
      
      try {
        const yaml = require('yaml');
        const parsed = yaml.parse(frontMatterMatch[1]);
        
        if (parsed.name && parsed.agent_type) {
          console.log(`   ✅ Valid agent configuration: ${parsed.name} (${parsed.agent_type})`);
        } else {
          console.log('   ❌ Invalid agent configuration structure');
        }
      } catch (error) {
        console.log(`   ❌ YAML parsing failed: ${error.message}`);
      }
    } else {
      console.log('   ❌ No front matter found in agent configuration');
    }

    // Test 3: Check TypeScript compilation readiness
    console.log('\n3. Checking TypeScript source files...');
    
    const srcFiles = [
      '../src/types/configuration.ts',
      '../src/config/configuration-manager.ts',
      '../src/utils/markdown-parser.ts',
      '../src/loaders/agent-definition-loader.ts',
      '../src/loaders/command-definition-loader.ts',
      '../src/commands/configuration.ts'
    ];
    
    let allFilesExist = true;
    
    for (const file of srcFiles) {
      const filePath = path.join(__dirname, file);
      if (fs.existsSync(filePath)) {
        console.log(`   ✅ ${path.basename(file)} exists`);
      } else {
        console.log(`   ❌ ${path.basename(file)} missing`);
        allFilesExist = false;
      }
    }
    
    if (allFilesExist) {
      console.log('   ✅ All core TypeScript files are present');
    }

    // Test 4: Check package.json dependencies
    console.log('\n4. Checking package.json dependencies...');
    
    const packageJsonPath = path.join(__dirname, '../package.json');
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    
    const requiredDeps = ['yaml', 'chalk', 'ora', 'table', 'commander'];
    let allDepsPresent = true;
    
    for (const dep of requiredDeps) {
      if (packageJson.dependencies[dep]) {
        console.log(`   ✅ ${dep} dependency found`);
      } else {
        console.log(`   ❌ ${dep} dependency missing`);
        allDepsPresent = false;
      }
    }
    
    if (allDepsPresent) {
      console.log('   ✅ All required dependencies are present');
    }

    // Test 5: CLI integration check
    console.log('\n5. Checking CLI integration...');
    
    const indexPath = path.join(__dirname, '../src/index.ts');
    const indexContent = fs.readFileSync(indexPath, 'utf8');
    
    if (indexContent.includes('configuration.listAgents')) {
      console.log('   ✅ Agent listing command integrated');
    } else {
      console.log('   ❌ Agent listing command not integrated');
    }
    
    if (indexContent.includes('configuration.doctor')) {
      console.log('   ✅ Doctor command integrated');
    } else {
      console.log('   ❌ Doctor command not integrated');
    }

    console.log('\n🎉 Configuration system test completed!');
    console.log('\n📝 Next steps:');
    console.log('   1. Run "npm run build" to compile TypeScript');
    console.log('   2. Run "mcp init" to create configuration directories');
    console.log('   3. Run "mcp list agents" to see available agents');
    console.log('   4. Run "mcp doctor" to validate configurations');

  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    process.exit(1);
  }
}

// Run the test
testConfigurationSystem().catch(console.error);