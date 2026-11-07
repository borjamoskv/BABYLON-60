import type { ComponentProps } from "react";
import type { BabylonMasterclass } from "../src/BabylonMasterclass";
import payload from "../public/payload.json";

// Check the shipped asset against the real component props, without a cast.
const checked: ComponentProps<typeof BabylonMasterclass> = payload;
export default checked;
