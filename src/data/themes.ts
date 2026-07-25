// C5-REAL EXERGY CERTIFIED
export interface Theme {
  id: string;
  name: string;
  bg: string;
  surface: string;
  border: string;
  accent: string;
  text: string;
  muted: string;
  lapis: string;
  gold: string;
  verify: string;
  breakColor: string;
}

export const THEMES: Record<string, Theme> = {
  awwwards: {
    id: 'awwwards',
    name: 'YInMn Noir',
    bg: '#090B19',
    surface: '#0F1226',
    border: '#2E3866',
    accent: '#3B4DFF',
    text: '#FFFFFF',
    muted: '#B4B9DF',
    lapis: '#3B4DFF',
    gold: '#F59E0B',
    verify: '#10B981',
    breakColor: '#EF4444'
  },
  sol: {
    id: 'sol',
    name: 'Sol Cinematic',
    bg: '#0D0D0F',
    surface: '#15151A',
    border: '#33291A',
    accent: '#F59E0B',
    text: '#F8FAFCE0',
    muted: '#94A3B8',
    lapis: '#3B4DFF',
    gold: '#F59E0B',
    verify: '#10B981',
    breakColor: '#EF4444'
  },
  obsidian: {
    id: 'obsidian',
    name: 'Obsidian Pulse',
    bg: '#030303',
    surface: '#0E0E10',
    border: '#26262B',
    accent: '#FF3366',
    text: '#F1F1F1',
    muted: '#808080',
    lapis: '#FF3366',
    gold: '#F59E0B',
    verify: '#10B981',
    breakColor: '#EF4444'
  },
  cyber: {
    id: 'cyber',
    name: 'Cyber Metallic',
    bg: '#050B14',
    surface: '#0B1526',
    border: '#1E3A5F',
    accent: '#00F0FF',
    text: '#E0F7FA',
    muted: '#64748B',
    lapis: '#00F0FF',
    gold: '#F59E0B',
    verify: '#10B981',
    breakColor: '#EF4444'
  }
};
