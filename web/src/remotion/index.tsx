import React from 'react';
import { registerRoot } from 'remotion';
import { RemotionVideoRoot } from './SubstackMafiaComposition';
import { GoedelBrosRoot } from './GoedelBrosComposition';

export const Babylon60Root: React.FC = () => {
  return (
    <>
      <RemotionVideoRoot />
      <GoedelBrosRoot />
    </>
  );
};

registerRoot(Babylon60Root);
