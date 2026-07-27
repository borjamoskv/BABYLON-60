/**
 * Fuzz test configuration helper
 * 
 * Parses CLI arguments and environment variables for fuzz test configuration.
 * CLI arguments take precedence over environment variables.
 */

export interface FuzzConfig {
  size: number;
  seed: number;
  multiBin?: boolean;
}

/**
 * Parse CLI arguments from process.argv
 * Supports: --size, --seed, --multi-bin
 */
function parseCliArgs(): Partial<FuzzConfig> {
  const args = process.argv.slice(2); // Skip node and script path
  const config: Partial<FuzzConfig> = {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    // Handle --size or --size=value
    if (arg === '--size' && i + 1 < args.length) {
      const value = parseInt(args[i + 1], 10);
      if (!isNaN(value)) {
        config.size = value;
        i++; // Skip next arg as it's the value
      }
    } else if (arg.startsWith('--size=')) {
      const value = parseInt(arg.split('=')[1], 10);
      if (!isNaN(value)) {
        config.size = value;
      }
    }
    
    // Handle --seed or --seed=value
    if (arg === '--seed' && i + 1 < args.length) {
      const value = parseInt(args[i + 1], 10);
      if (!isNaN(value)) {
        config.seed = value;
        i++; // Skip next arg as it's the value
      }
    } else if (arg.startsWith('--seed=')) {
      const value = parseInt(arg.split('=')[1], 10);
      if (!isNaN(value)) {
        config.seed = value;
      }
    }
    
    // Handle --multi-bin flag
    if (arg === '--multi-bin') {
      config.multiBin = true;
    }
  }

  return config;
}

/**
 * Get fuzz test configuration from CLI args or environment variables
 * CLI arguments take precedence over environment variables
 */
export function getFuzzConfig(): FuzzConfig {
  // Parse CLI arguments first
  const cliConfig = parseCliArgs();
  
  // Get defaults from environment variables
  // Validate parseInt results to avoid NaN (parseInt returns NaN for invalid input)
  const envSizeRaw = process.env.FUZZ_SIZE ? parseInt(process.env.FUZZ_SIZE, 10) : undefined;
  const envSize = envSizeRaw !== undefined && !isNaN(envSizeRaw) ? envSizeRaw : undefined;
  
  const envSeedRaw = process.env.RANDOM_SEED ? parseInt(process.env.RANDOM_SEED, 10) : undefined;
  const envSeed = envSeedRaw !== undefined && !isNaN(envSeedRaw) ? envSeedRaw : undefined;
  
  const envMultiBin = process.env.MULTI_BIN_MODE === 'true' ? true : undefined;
  
  // CLI args take precedence, fall back to env vars, then defaults
  return {
    size: cliConfig.size ?? envSize ?? 100,
    seed: cliConfig.seed ?? envSeed ?? Date.now(),
    multiBin: cliConfig.multiBin ?? envMultiBin ?? false,
  };
}

