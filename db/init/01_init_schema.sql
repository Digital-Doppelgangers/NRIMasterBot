USE `nrirpg`;

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
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS campaigns;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE campaigns (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  title VARCHAR(200) NOT NULL,
  description TEXT NULL,
  system_title VARCHAR(64) NULL,
  is_public BOOLEAN NOT NULL DEFAULT FALSE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  telegram_id BIGINT NOT NULL,
  username VARCHAR(64) NULL,
  display_name VARCHAR(128) NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'free',
  active_campaign_id BIGINT UNSIGNED NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uk_users_telegram_id (telegram_id),
  KEY idx_users_active_campaign_id (active_campaign_id),

  CONSTRAINT fk_users_active_campaign
    FOREIGN KEY (active_campaign_id) REFERENCES campaigns(id)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE campaign_members (
  campaign_id BIGINT UNSIGNED NOT NULL,
  user_id BIGINT UNSIGNED NOT NULL,
  role ENUM('owner', 'gm', 'player', 'viewer') NOT NULL DEFAULT 'player',

  PRIMARY KEY (campaign_id, user_id),
  KEY idx_campaign_members_user_id (user_id),

  CONSTRAINT fk_campaign_members_campaign
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  CONSTRAINT fk_campaign_members_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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

  PRIMARY KEY (id),
  KEY idx_characters_owner_user_id (owner_user_id),

  CONSTRAINT fk_characters_owner
    FOREIGN KEY (owner_user_id) REFERENCES users(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE campaign_characters (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  campaign_id BIGINT UNSIGNED NOT NULL,
  character_id BIGINT UNSIGNED NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  notes TEXT NULL,

  PRIMARY KEY (id),
  UNIQUE KEY uk_campaign_character_once (campaign_id, character_id),
  KEY idx_campaign_characters_campaign_id (campaign_id),
  KEY idx_campaign_characters_character_id (character_id),

  CONSTRAINT fk_campaign_characters_campaign
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  CONSTRAINT fk_campaign_characters_character
    FOREIGN KEY (character_id) REFERENCES characters(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE npcs (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  owner_user_id BIGINT UNSIGNED NOT NULL,
  campaign_id BIGINT UNSIGNED NULL,
  name VARCHAR(128) NULL,
  role VARCHAR(64) NULL,
  description TEXT NULL,
  max_hp INT NULL,
  current_hp INT NULL,
  armor_class INT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  KEY idx_npcs_owner_user_id (owner_user_id),
  KEY idx_npcs_campaign_id (campaign_id),

  CONSTRAINT fk_npcs_owner
    FOREIGN KEY (owner_user_id) REFERENCES users(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  CONSTRAINT fk_npcs_campaign
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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

  PRIMARY KEY (id),
  KEY idx_abilities_character_id (character_id),

  CONSTRAINT fk_abilities_character
    FOREIGN KEY (character_id) REFERENCES characters(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ability_control (
  ability_id BIGINT UNSIGNED NOT NULL,
  control_type ENUM('charm', 'blind', 'stun', 'fear', 'slow', 'silence', 'push', 'prone') NOT NULL,
  duration_rounds INT NOT NULL,
  condition_end VARCHAR(255) NOT NULL,

  PRIMARY KEY (ability_id),

  CONSTRAINT fk_ability_control_ability
    FOREIGN KEY (ability_id) REFERENCES abilities(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
