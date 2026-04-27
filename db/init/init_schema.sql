CREATE DATABASE IF NOT EXISTS `NRP-RPG` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `NRP-RPG`;
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS ability_support;
DROP TABLE IF EXISTS ability_control;
DROP TABLE IF EXISTS ability_damage;
DROP TABLE IF EXISTS abilities;
DROP TABLE IF EXISTS campaign_characters;
DROP TABLE IF EXISTS npcs;
DROP TABLE IF EXISTS characters;
DROP TABLE IF EXISTS campaign_members;
DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  telegram_id BIGINT NOT NULL,
  username VARCHAR(64) NULL,
  display_name VARCHAR(128) NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'free',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_seen_at DATETIME NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_users_telegram_id (telegram_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE campaigns (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  title VARCHAR(200) NOT NULL,
  description TEXT NULL,
  system_title VARCHAR(64) NULL,
  is_public BOOLEAN NOT NULL DEFAULT FALSE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE campaign_members (
  campaign_id BIGINT UNSIGNED NOT NULL,
  user_id BIGINT UNSIGNED NOT NULL,
  role ENUM('owner', 'gm', 'player', 'viewer') NOT NULL DEFAULT 'player',
  joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (campaign_id, user_id),
  CONSTRAINT fk_cm_campaign
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_cm_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE characters (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  owner_user_id BIGINT UNSIGNED NOT NULL,
  name VARCHAR(128) NOT NULL,
  gender ENUM('male', 'female', 'other') NULL,
  age INT NULL,
  race VARCHAR(64) NULL,
  `class` VARCHAR(64) NULL,
  subclass VARCHAR(64) NULL,
  background VARCHAR(128) NULL,
  alignment VARCHAR(64) NULL,
  level INT NOT NULL DEFAULT 1,
  hp_base INT NULL,
  max_hp INT NULL,
  current_hp INT NULL,
  ac_base INT NULL,
  armor_class INT NULL,
  str_mod TINYINT NULL,
  dex_mod TINYINT NULL,
  con_mod TINYINT NULL,
  int_mod TINYINT NULL,
  wis_mod TINYINT NULL,
  cha_mod TINYINT NULL,
  backstory TEXT NULL,
  lifecycle_status ENUM('available', 'in_campaign', 'archived') NOT NULL DEFAULT 'available',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT fk_char_owner
    FOREIGN KEY (owner_user_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT chk_char_level CHECK (level >= 1),
  CONSTRAINT chk_char_hp_nonnegative CHECK (
    (hp_base IS NULL OR hp_base >= 0) AND
    (max_hp IS NULL OR max_hp >= 0) AND
    (current_hp IS NULL OR current_hp >= 0) AND
    (armor_class IS NULL OR armor_class >= 0)
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE campaign_characters (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  campaign_id BIGINT UNSIGNED NOT NULL,
  character_id BIGINT UNSIGNED NOT NULL,
  joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  left_at DATETIME NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  notes TEXT NULL,
  active_character_id BIGINT UNSIGNED GENERATED ALWAYS AS (
    CASE WHEN is_active THEN character_id ELSE NULL END
  ) STORED,
  PRIMARY KEY (id),
  UNIQUE KEY uk_campaign_character_once (campaign_id, character_id),
  UNIQUE KEY uk_character_single_active (active_character_id),
  CONSTRAINT fk_cc_campaign
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_cc_character
    FOREIGN KEY (character_id) REFERENCES characters(id)
    ON DELETE CASCADE,
  CONSTRAINT chk_cc_dates CHECK (left_at IS NULL OR left_at >= joined_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE npcs (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  campaign_id BIGINT UNSIGNED NOT NULL,
  name VARCHAR(128) NOT NULL,
  role VARCHAR(64) NULL,
  description TEXT NULL,
  max_hp INT NULL,
  current_hp INT NULL,
  armor_class INT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT fk_npc_campaign
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE abilities (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  character_id BIGINT UNSIGNED NOT NULL,
  name VARCHAR(128) NOT NULL,
  ability_kind ENUM('attack', 'control', 'strong_attack', 'support') NOT NULL,
  usage_limit ENUM('at_will', '1/combat', '2/short_rest', '1/rest') NOT NULL,
  range_shape ENUM('touch', 'melee', 'ranged', 'cone', 'line', 'sphere') NOT NULL,
  range_distance_m DECIMAL(6,2) NOT NULL,
  bonus_ability ENUM('str', 'dex', 'con', 'int', 'wis', 'cha') NOT NULL,
  description VARCHAR(500) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT fk_ability_character
    FOREIGN KEY (character_id) REFERENCES characters(id)
    ON DELETE CASCADE,
  CONSTRAINT chk_ability_range CHECK (range_distance_m >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ability_damage (
  ability_id BIGINT UNSIGNED NOT NULL,
  dice VARCHAR(16) NOT NULL,
  damage_type ENUM(
    'slashing', 'piercing', 'bludgeoning',
    'fire', 'cold', 'lightning', 'poison', 'acid',
    'psychic', 'necrotic', 'radiant', 'thunder'
  ) NOT NULL,
  PRIMARY KEY (ability_id),
  CONSTRAINT fk_ability_damage_ability
    FOREIGN KEY (ability_id) REFERENCES abilities(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ability_control (
  ability_id BIGINT UNSIGNED NOT NULL,
  control_type ENUM('charm', 'blind', 'stun', 'fear', 'slow', 'silence', 'push', 'prone') NOT NULL,
  duration_rounds INT NOT NULL,
  condition_end VARCHAR(255) NOT NULL,
  PRIMARY KEY (ability_id),
  CONSTRAINT fk_ability_control_ability
    FOREIGN KEY (ability_id) REFERENCES abilities(id)
    ON DELETE CASCADE,
  CONSTRAINT chk_control_duration CHECK (duration_rounds >= 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ability_support (
  ability_id BIGINT UNSIGNED NOT NULL,
  support_type ENUM('heal', 'buff_roll', 'buff_damage', 'buff_to_hit', 'extra_action', 'cleanse') NOT NULL,
  check_dc INT NULL,
  check_attr ENUM('str', 'dex', 'con', 'int', 'wis', 'cha') NULL,
  dice VARCHAR(16) NULL,
  action_type ENUM('bonus_action', 'reaction', 'move') NULL,
  cleanse_target ENUM('blind', 'fear', 'charm', 'stun', 'slow', 'silence', 'prone') NULL,
  notes VARCHAR(255) NULL,
  PRIMARY KEY (ability_id),
  CONSTRAINT fk_ability_support_ability
    FOREIGN KEY (ability_id) REFERENCES abilities(id)
    ON DELETE CASCADE,
  CONSTRAINT chk_support_dc CHECK (check_dc IS NULL OR check_dc >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_characters_owner_user_id ON characters(owner_user_id);
CREATE INDEX idx_campaign_members_user_id ON campaign_members(user_id);
CREATE INDEX idx_campaign_characters_campaign_id ON campaign_characters(campaign_id);
CREATE INDEX idx_campaign_characters_character_id ON campaign_characters(character_id);
CREATE INDEX idx_abilities_character_id ON abilities(character_id);
CREATE INDEX idx_npcs_campaign_id ON npcs(campaign_id);

SET FOREIGN_KEY_CHECKS = 1;