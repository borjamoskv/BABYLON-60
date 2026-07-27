// === Storage Utility ===
const PREFIX = 'twinforge_';

export const storage = {
  get(key, fallback = null) {
    try {
      const raw = localStorage.getItem(PREFIX + key);
      return raw ? JSON.parse(raw) : fallback;
    } catch { return fallback; }
  },

  set(key, value) {
    try { localStorage.setItem(PREFIX + key, JSON.stringify(value)); } catch {}
  },

  getProfile() {
    return this.get('active_profile', null);
  },

  setProfile(name) {
    this.set('active_profile', name);
  },

  getProfileData(profile) {
    return this.get(`profile_${profile}`, {
      completedMissions: [],
      achievements: [],
      files: {},
      stats: { totalRuns: 0, totalLines: 0, errorFreeStreak: 0, sessionStart: null },
    });
  },

  saveProfileData(profile, data) {
    this.set(`profile_${profile}`, data);
  },

  completeMission(profile, missionId) {
    const data = this.getProfileData(profile);
    if (!data.completedMissions.includes(missionId)) {
      data.completedMissions.push(missionId);
    }
    this.saveProfileData(profile, data);
    return data;
  },

  unlockAchievement(profile, achievementId) {
    const data = this.getProfileData(profile);
    if (!data.achievements.includes(achievementId)) {
      data.achievements.push(achievementId);
      this.saveProfileData(profile, data);
      return true; // newly unlocked
    }
    return false;
  },

  updateStats(profile, updates) {
    const data = this.getProfileData(profile);
    Object.assign(data.stats, updates);
    this.saveProfileData(profile, data);
    return data.stats;
  },

  saveFile(profile, filename, content) {
    const data = this.getProfileData(profile);
    data.files[filename] = content;
    this.saveProfileData(profile, data);
  },

  getFile(profile, filename) {
    const data = this.getProfileData(profile);
    return data.files[filename] || null;
  }
};
