-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 13, 2026 at 06:34 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.1.25

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

CREATE DATABASE IF NOT EXISTS hazardhub;
USE hazardhub;

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `hazardhub`
--

-- --------------------------------------------------------

--
-- Table structure for table `admin_users`
--

CREATE TABLE `admin_users` (
  `id` int(10) UNSIGNED NOT NULL,
  `username` varchar(80) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `full_name` varchar(150) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `last_login` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `admin_users`
--

INSERT INTO `admin_users` (`id`, `username`, `password_hash`, `full_name`, `is_active`, `last_login`, `created_at`, `updated_at`) VALUES
(1, 'admin@hazardhub.com', 'scrypt:32768:8:1$q7oPMxgmAdR1J7mO$843bfc3d334df70f586b2da9d1a2bf59385b1fa95a4a5013ff2efc30ad14d2dafb674cefdf1f99f49c419d873d14c90a908c427c5fe2f7c95b0afa20a2570aef', 'System Administrator', 1, NULL, '2026-02-17 20:33:45', '2026-02-19 11:48:43');

-- --------------------------------------------------------

--
-- Table structure for table `certificates`
--

CREATE TABLE `certificates` (
  `id` int(10) UNSIGNED NOT NULL,
  `file_name` varchar(255) NOT NULL,
  `file_path` varchar(500) DEFAULT NULL,
  `uploaded_by` int(10) UNSIGNED DEFAULT NULL,
  `uploaded_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `cert_files`
--

CREATE TABLE `cert_files` (
  `id` int(10) UNSIGNED NOT NULL,
  `folder_id` int(10) UNSIGNED NOT NULL,
  `filename` varchar(255) NOT NULL,
  `original_name` varchar(255) NOT NULL,
  `file_size` varchar(30) DEFAULT '',
  `mime_type` varchar(100) DEFAULT '',
  `uploaded_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `cert_folders`
--

CREATE TABLE `cert_folders` (
  `id` int(10) UNSIGNED NOT NULL,
  `name` varchar(100) NOT NULL,
  `emoji` varchar(255) DEFAULT '?',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `created_by` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `concern_reports`
--

CREATE TABLE `concern_reports` (
  `id` int(10) UNSIGNED NOT NULL,
  `report_date` date NOT NULL,
  `report_time` time DEFAULT NULL,
  `report_type` enum('Hazard','Concern/Suggestion') NOT NULL,
  `reported_by` varchar(150) DEFAULT NULL,
  `is_anonymous` tinyint(1) NOT NULL DEFAULT 0,
  `status` enum('pending','resolved','open','in_progress','rejected') DEFAULT 'pending',
  `incident_location` varchar(200) DEFAULT NULL,
  `inspected_by` varchar(150) DEFAULT NULL,
  `hazard_description` text DEFAULT NULL,
  `hazard_image_path` varchar(500) DEFAULT NULL,
  `risk_level` enum('Low','Medium','High','Critical') DEFAULT NULL,
  `concern_description` text DEFAULT NULL,
  `suggestion_text` text DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `nb_confidence` float DEFAULT NULL,
  `nb_scores` text DEFAULT NULL,
  `admin_remarks` text DEFAULT NULL,
  `ehs_officer` varchar(150) DEFAULT NULL,
  `resolved_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `emergency_lights`
--

CREATE TABLE `emergency_lights` (
  `id` int(10) UNSIGNED NOT NULL,
  `location_area` varchar(200) NOT NULL DEFAULT '',
  `no_obstruction` enum('OK','NG','NA') DEFAULT NULL,
  `light_functional` enum('OK','NG','NA') DEFAULT NULL,
  `battery_backup` enum('OK','NG','NA') DEFAULT NULL,
  `charge_indicator` enum('OK','NG','NA') DEFAULT NULL,
  `physical_damage` enum('OK','NG','NA') DEFAULT NULL,
  `inspected_by` varchar(120) NOT NULL DEFAULT '',
  `date_inspected` date DEFAULT NULL,
  `remark` text DEFAULT NULL,
  `picture_path` varchar(300) NOT NULL DEFAULT '',
  `created_by_user_id` int(10) UNSIGNED DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `employee_accounts`
--

CREATE TABLE `employee_accounts` (
  `id` int(10) UNSIGNED NOT NULL,
  `employee_id` varchar(20) NOT NULL,
  `full_name` varchar(150) NOT NULL,
  `email` varchar(200) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` varchar(80) DEFAULT NULL,
  `position_in_company` varchar(120) DEFAULT NULL,
  `department` varchar(120) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `fire_equipment`
--

CREATE TABLE `fire_equipment` (
  `id` int(10) UNSIGNED NOT NULL,
  `equipment_type` enum('Extinguisher','Emergency Light','Hose Cabinet') NOT NULL,
  `location_area` varchar(200) NOT NULL,
  `description` varchar(200) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `fire_extinguishers`
--

CREATE TABLE `fire_extinguishers` (
  `id` int(10) UNSIGNED NOT NULL,
  `location_area` varchar(200) NOT NULL DEFAULT '',
  `type` varchar(80) NOT NULL DEFAULT '',
  `capacity` varchar(40) NOT NULL DEFAULT '',
  `no_obstruction` enum('OK','NG','NA') DEFAULT NULL,
  `label_visible` enum('OK','NG','NA') DEFAULT NULL,
  `safety_pin` enum('OK','NG','NA') DEFAULT NULL,
  `tag_in_place` enum('OK','NG','NA') DEFAULT NULL,
  `pressure_gauge` enum('OK','NG','NA') DEFAULT NULL,
  `no_physical_damage` enum('OK','NG','NA') DEFAULT NULL,
  `expired_date` date DEFAULT NULL,
  `inspected_by` varchar(120) NOT NULL DEFAULT '',
  `date_inspected` date DEFAULT NULL,
  `remark` text DEFAULT NULL,
  `picture_path` varchar(300) NOT NULL DEFAULT '',
  `created_by_user_id` int(10) UNSIGNED DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `fire_hose_cabinets`
--

CREATE TABLE `fire_hose_cabinets` (
  `id` int(10) UNSIGNED NOT NULL,
  `location_area` varchar(200) NOT NULL DEFAULT '',
  `no_obstruction` enum('OK','NG','NA') DEFAULT NULL,
  `glass_condition` enum('OK','NG','NA') DEFAULT NULL,
  `hose_condition` enum('OK','NG','NA') DEFAULT NULL,
  `nozzle_condition` enum('OK','NG','NA') DEFAULT NULL,
  `axe_condition` enum('OK','NG','NA') DEFAULT NULL,
  `valve_condition` enum('OK','NG','NA') DEFAULT NULL,
  `cabinet_condition` enum('OK','NG','NA') DEFAULT NULL,
  `inspected_by` varchar(120) NOT NULL DEFAULT '',
  `date_inspected` date DEFAULT NULL,
  `remark` text DEFAULT NULL,
  `picture_path` varchar(300) NOT NULL DEFAULT '',
  `created_by_user_id` int(10) UNSIGNED DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `fire_inspection_extinguisher`
--

CREATE TABLE `fire_inspection_extinguisher` (
  `id` int(10) UNSIGNED NOT NULL,
  `equipment_id` int(10) UNSIGNED DEFAULT NULL,
  `location_area` varchar(200) DEFAULT NULL,
  `extinguisher_type` varchar(80) DEFAULT NULL,
  `capacity_lbs` decimal(6,2) DEFAULT NULL,
  `no_obstruction` tinyint(1) DEFAULT NULL,
  `label_visible` tinyint(1) DEFAULT NULL,
  `safety_pin` tinyint(1) DEFAULT NULL,
  `tag_in_place` tinyint(1) DEFAULT NULL,
  `pressure_gauge` enum('Full','Half','Low','Empty') DEFAULT NULL,
  `no_physical_damage` tinyint(1) DEFAULT NULL,
  `expired_date` date DEFAULT NULL,
  `inspected_by` varchar(150) DEFAULT NULL,
  `date_inspected` date NOT NULL,
  `remark` text DEFAULT NULL,
  `picture_path` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `fire_inspection_hose`
--

CREATE TABLE `fire_inspection_hose` (
  `id` int(10) UNSIGNED NOT NULL,
  `equipment_id` int(10) UNSIGNED DEFAULT NULL,
  `location_area` varchar(200) DEFAULT NULL,
  `no_obstruction` tinyint(1) DEFAULT NULL,
  `glass_intact` tinyint(1) DEFAULT NULL,
  `hose_condition` enum('Good','Fair','Poor') DEFAULT NULL,
  `nozzle_condition` enum('Good','Fair','Poor') DEFAULT NULL,
  `axe_present` tinyint(1) DEFAULT NULL,
  `valve_condition` enum('Good','Fair','Poor') DEFAULT NULL,
  `cabinet_condition` enum('Good','Fair','Poor') DEFAULT NULL,
  `inspected_by` varchar(150) DEFAULT NULL,
  `date_inspected` date NOT NULL,
  `remark` text DEFAULT NULL,
  `picture_path` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `fire_inspection_light`
--

CREATE TABLE `fire_inspection_light` (
  `id` int(10) UNSIGNED NOT NULL,
  `equipment_id` int(10) UNSIGNED DEFAULT NULL,
  `location_area` varchar(200) DEFAULT NULL,
  `no_obstruction` tinyint(1) DEFAULT NULL,
  `light_functional` tinyint(1) DEFAULT NULL,
  `battery_backup` tinyint(1) DEFAULT NULL,
  `charge_indicator` tinyint(1) DEFAULT NULL,
  `no_physical_damage` tinyint(1) DEFAULT NULL,
  `inspected_by` varchar(150) DEFAULT NULL,
  `date_inspected` date NOT NULL,
  `remark` text DEFAULT NULL,
  `picture_path` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `fire_protection_inspections`
--

CREATE TABLE `fire_protection_inspections` (
  `id` int(11) NOT NULL,
  `inspection_type` varchar(50) NOT NULL,
  `location` varchar(120) DEFAULT '',
  `extinguisher_type` varchar(80) DEFAULT '',
  `capacity` varchar(30) DEFAULT '',
  `expiry_date` varchar(20) DEFAULT '',
  `inspected_by` varchar(120) DEFAULT '',
  `inspection_date` varchar(20) DEFAULT '',
  `remark` text DEFAULT '',
  `checklist_ok` text DEFAULT '',
  `checklist_ng` text DEFAULT '',
  `photo_filename` varchar(255) DEFAULT '',
  `user_id` int(11) DEFAULT NULL,
  `submitted_at` varchar(50) DEFAULT '',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `hazard_reports`
--

CREATE TABLE `hazard_reports` (
  `id` int(11) NOT NULL,
  `date` varchar(20) NOT NULL,
  `time` varchar(10) DEFAULT '',
  `location` varchar(120) DEFAULT '',
  `reported_by` varchar(120) DEFAULT '',
  `main_hazard_type` varchar(50) DEFAULT '',
  `hazard_categories` text DEFAULT '',
  `hazard_details` text DEFAULT '',
  `description` text DEFAULT '',
  `risk_level` varchar(30) DEFAULT 'Medium',
  `ai_priority` varchar(30) DEFAULT 'Medium',
  `status` enum('pending','resolved','open','in_progress','rejected') DEFAULT 'pending',
  `photo_filename` varchar(255) DEFAULT '',
  `submitted_by_user` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `nb_confidence` float DEFAULT NULL,
  `nb_scores` text DEFAULT NULL,
  `admin_remarks` text DEFAULT NULL,
  `ehs_officer` varchar(150) DEFAULT NULL,
  `resolved_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `incidents`
--

CREATE TABLE `incidents` (
  `id` int(10) UNSIGNED NOT NULL,
  `control_no` varchar(30) NOT NULL,
  `incident_date` date NOT NULL,
  `incident_time` time DEFAULT NULL,
  `employee_id` int(10) UNSIGNED DEFAULT NULL,
  `employee_name` varchar(150) DEFAULT NULL,
  `classification` enum('Near Miss','First Aid','Minor','Major','Damage to Property') NOT NULL,
  `description` text DEFAULT NULL,
  `incident_location` varchar(200) DEFAULT NULL,
  `reported_by` varchar(150) DEFAULT NULL,
  `status` enum('Open','Under Investigation','Resolved','Closed') NOT NULL DEFAULT 'Open',
  `created_by` int(10) UNSIGNED DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `investigation_body_parts`
--

CREATE TABLE `investigation_body_parts` (
  `id` int(10) UNSIGNED NOT NULL,
  `report_id` int(10) UNSIGNED NOT NULL,
  `body_part` enum('Head','Front Neck','Back Neck','Chest','Abdomen','Upper Back','Lower Back','Left Arm','Left Forearm','Left Hand','Left Thigh','Left Leg','Left Foot','Right Arm','Right Forearm','Right Hand','Right Thigh','Right Leg','Right Foot','Buttocks','Groin') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `investigation_reports`
--

CREATE TABLE `investigation_reports` (
  `id` int(10) UNSIGNED NOT NULL,
  `incident_id` int(10) UNSIGNED DEFAULT NULL,
  `establishment` varchar(200) DEFAULT NULL,
  `employer_address` text DEFAULT NULL,
  `nature_of_business` varchar(200) DEFAULT NULL,
  `employer_name` varchar(150) DEFAULT NULL,
  `employer_nationality` varchar(80) DEFAULT NULL,
  `num_employees_male` smallint(5) UNSIGNED DEFAULT 0,
  `num_employees_female` smallint(5) UNSIGNED DEFAULT 0,
  `num_employees_total` smallint(5) UNSIGNED DEFAULT 0,
  `injured_name` varchar(150) DEFAULT NULL,
  `injured_age` tinyint(3) UNSIGNED DEFAULT NULL,
  `injured_sex` enum('Male','Female','Other') DEFAULT NULL,
  `injured_civil_status` varchar(40) DEFAULT NULL,
  `injured_address` text DEFAULT NULL,
  `employment_status` enum('Regular','Contractual','Probationary','Casual') DEFAULT NULL,
  `employment_no` varchar(50) DEFAULT NULL,
  `affiliated_org` varchar(200) DEFAULT NULL,
  `date_hired` date DEFAULT NULL,
  `division_section` varchar(120) DEFAULT NULL,
  `position` varchar(120) DEFAULT NULL,
  `immediate_superior` varchar(150) DEFAULT NULL,
  `superior_position` varchar(120) DEFAULT NULL,
  `avg_weekly_wage` decimal(12,2) DEFAULT NULL,
  `num_dependents` tinyint(3) UNSIGNED DEFAULT NULL,
  `service_length` varchar(80) DEFAULT NULL,
  `occupation` varchar(120) DEFAULT NULL,
  `years_experience` tinyint(3) UNSIGNED DEFAULT NULL,
  `shift_start` time DEFAULT NULL,
  `shift_end` time DEFAULT NULL,
  `hours_per_day` decimal(4,1) DEFAULT NULL,
  `days_per_week` decimal(3,1) DEFAULT NULL,
  `reportable_illness` varchar(200) DEFAULT NULL,
  `covid_fatal` tinyint(1) DEFAULT NULL,
  `work_location` enum('Office','Field','Factory','Warehouse') DEFAULT NULL,
  `illness_date_begun` date DEFAULT NULL,
  `illness_return_date` date DEFAULT NULL,
  `illness_day_changed` varchar(80) DEFAULT NULL,
  `illness_day_lost` smallint(5) UNSIGNED DEFAULT NULL,
  `accident_date` date DEFAULT NULL,
  `accident_time` time DEFAULT NULL,
  `accident_location` varchar(200) DEFAULT NULL,
  `accident_involved` enum('Worker','Machinery','Both','Other') DEFAULT NULL,
  `accident_involved_other` varchar(150) DEFAULT NULL,
  `accident_description` text DEFAULT NULL,
  `doing_regular_job` tinyint(1) DEFAULT NULL,
  `not_regular_reason` varchar(200) DEFAULT NULL,
  `extent_of_disability` varchar(120) DEFAULT NULL,
  `nature_of_injury` enum('Fracture','Sprain','Laceration','Burn','Contusion','Amputation') DEFAULT NULL,
  `type_of_contact` varchar(120) DEFAULT NULL,
  `disability_date_begun` date DEFAULT NULL,
  `disability_return_date` date DEFAULT NULL,
  `disability_day_changed` varchar(80) DEFAULT NULL,
  `days_lost` smallint(5) UNSIGNED DEFAULT NULL,
  `agency_involved` varchar(200) DEFAULT NULL,
  `agency_part_involved` varchar(200) DEFAULT NULL,
  `accident_type` enum('Fall','Struck by object','Caught in/between','Overexertion','Contact with electricity','Exposure to chemicals','Other') DEFAULT NULL,
  `unsafe_condition` varchar(200) DEFAULT NULL,
  `unsafe_act` varchar(200) DEFAULT NULL,
  `contributing_factor` varchar(200) DEFAULT NULL,
  `rca_activity` varchar(200) DEFAULT NULL,
  `rca_job_relevant` tinyint(1) DEFAULT NULL,
  `rca_equip_condition` tinyint(1) DEFAULT NULL,
  `rca_equip_reason` varchar(200) DEFAULT NULL,
  `rca_safeguard_provided` tinyint(1) DEFAULT NULL,
  `rca_supervision` tinyint(1) DEFAULT NULL,
  `rca_supervisor_name` varchar(200) DEFAULT NULL,
  `rca_instructions` tinyint(1) DEFAULT NULL,
  `rca_training` tinyint(1) DEFAULT NULL,
  `rca_ppe_provided` tinyint(1) DEFAULT NULL,
  `rca_ppe_used` tinyint(1) DEFAULT NULL,
  `rca_factor_type` enum('Unsafe Act','Unsafe Condition') DEFAULT NULL,
  `rca_leadership` enum('Yes','No','N/A') DEFAULT NULL,
  `rca_engineering` enum('Yes','No','N/A') DEFAULT NULL,
  `rca_purchasing` enum('Yes','No','N/A') DEFAULT NULL,
  `rca_physical_capacity` enum('Yes','No','N/A') DEFAULT NULL,
  `rca_mental_capability` enum('Yes','No','N/A') DEFAULT NULL,
  `rca_physio_stress` enum('Yes','No','N/A') DEFAULT NULL,
  `rca_lack_knowledge` enum('Yes','No','N/A') DEFAULT NULL,
  `rca_lack_skill` enum('Yes','No','N/A') DEFAULT NULL,
  `preventive_measures` text DEFAULT NULL,
  `safeguards_in_use` tinyint(1) DEFAULT NULL,
  `safeguards_reason` varchar(200) DEFAULT NULL,
  `control_instituted` varchar(200) DEFAULT NULL,
  `engineering_control` varchar(200) DEFAULT NULL,
  `engineering_cost` decimal(12,2) DEFAULT NULL,
  `admin_control` varchar(200) DEFAULT NULL,
  `admin_cost` decimal(12,2) DEFAULT NULL,
  `ppe_control` varchar(200) DEFAULT NULL,
  `ppe_cost` decimal(12,2) DEFAULT NULL,
  `compensation` decimal(12,2) DEFAULT NULL,
  `medical_cost` decimal(12,2) DEFAULT NULL,
  `burial_cost` decimal(12,2) DEFAULT NULL,
  `time_lost_injury_hrs` decimal(6,2) DEFAULT NULL,
  `time_lost_injury_mins` decimal(6,2) DEFAULT NULL,
  `time_lost_subsequent_hrs` decimal(6,2) DEFAULT NULL,
  `time_lost_subsequent_mins` decimal(6,2) DEFAULT NULL,
  `light_work_days` decimal(6,1) DEFAULT NULL,
  `machinery_damage` text DEFAULT NULL,
  `machinery_repair_cost` decimal(12,2) DEFAULT NULL,
  `machinery_lost_time` varchar(80) DEFAULT NULL,
  `machinery_lost_cost` decimal(12,2) DEFAULT NULL,
  `materials_damage` text DEFAULT NULL,
  `materials_repair_cost` decimal(12,2) DEFAULT NULL,
  `materials_lost_time` varchar(80) DEFAULT NULL,
  `materials_lost_cost` decimal(12,2) DEFAULT NULL,
  `equipment_damage` text DEFAULT NULL,
  `equipment_repair_cost` decimal(12,2) DEFAULT NULL,
  `equipment_lost_time` varchar(80) DEFAULT NULL,
  `equipment_lost_cost` decimal(12,2) DEFAULT NULL,
  `report_date` date DEFAULT NULL,
  `signed_oh_personnel` varchar(150) DEFAULT NULL,
  `signed_employer` varchar(150) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--

CREATE TABLE `notifications` (
  `id` int(11) NOT NULL,
  `date` varchar(20) NOT NULL,
  `severity` varchar(20) DEFAULT 'low',
  `message` text DEFAULT '',
  `location` varchar(120) DEFAULT '',
  `user_id` int(11) DEFAULT NULL,
  `is_read` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `notification_alerts`
--

CREATE TABLE `notification_alerts` (
  `id` int(10) UNSIGNED NOT NULL,
  `alert_date` date NOT NULL,
  `severity` enum('Low','Medium','High','Critical') NOT NULL DEFAULT 'Medium',
  `message` text NOT NULL,
  `location` varchar(200) DEFAULT NULL,
  `is_read` tinyint(1) NOT NULL DEFAULT 0,
  `related_incident_id` int(10) UNSIGNED DEFAULT NULL,
  `related_concern_id` int(10) UNSIGNED DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(10) UNSIGNED NOT NULL,
  `full_name` varchar(120) NOT NULL DEFAULT '',
  `email` varchar(180) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('Admin','Employee') NOT NULL DEFAULT 'Employee',
  `position` varchar(120) NOT NULL DEFAULT '',
  `id_number` varchar(20) NOT NULL DEFAULT '',
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `age` tinyint(3) UNSIGNED DEFAULT NULL COMMENT 'Employee age',
  `sex` enum('Male','Female','Other') DEFAULT NULL,
  `civil_status` enum('Single','Married','Widowed','Separated','Divorced') DEFAULT NULL,
  `employment_status` enum('Regular','Probationary','Contractual','Part-time','OJT') DEFAULT NULL,
  `supervisor_name` varchar(150) DEFAULT NULL COMMENT 'Immediate supervisor full name',
  `supervisor_position` varchar(150) DEFAULT NULL COMMENT 'Immediate supervisor position/title',
  `profile_complete` tinyint(1) NOT NULL DEFAULT 0 COMMENT '1 once employee has saved their own info',
  `profile_updated_at` datetime DEFAULT NULL COMMENT 'Last time employee self-updated'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `full_name`, `email`, `password_hash`, `role`, `position`, `id_number`, `is_active`, `created_at`, `updated_at`, `age`, `sex`, `civil_status`, `employment_status`, `supervisor_name`, `supervisor_position`, `profile_complete`, `profile_updated_at`) VALUES
(1, 'Administrator', 'admin@hazardhub.com', 'scrypt:32768:8:1$YS5u9Fi4JOeJ59u6$6ed43da2fef9b927cd0a9335f1bd1af49bc127d828cfb014f2336879c23f8ff6ad391df3fb7a83fdf52c035b1c156c971973b859844c69920a30f8772359d506', 'Admin', 'Safety Officer', 'ADMIN-00001', 1, '2026-03-13 08:48:37', '2026-03-13 08:48:37', NULL, NULL, NULL, NULL, NULL, NULL, 0, NULL);

-- --------------------------------------------------------

--
-- Stand-in structure for view `vw_concern_overview`
-- (See below for the actual view)
--
CREATE TABLE `vw_concern_overview` (
`hazard_count` decimal(22,0)
,`suggestion_count` decimal(22,0)
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `vw_dashboard_stats`
-- (See below for the actual view)
--
CREATE TABLE `vw_dashboard_stats` (
`total_incidents` bigint(21)
,`hazards_identified` bigint(21)
,`resolved_incidents` bigint(21)
,`pending_incidents` bigint(21)
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `vw_fire_inspection_counts`
-- (See below for the actual view)
--
CREATE TABLE `vw_fire_inspection_counts` (
`extinguisher_count` bigint(21)
,`light_count` bigint(21)
,`hose_count` bigint(21)
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `vw_hazard_concern_list`
-- (See below for the actual view)
--
CREATE TABLE `vw_hazard_concern_list` (
`id` int(10) unsigned
,`date` date
,`time` time
,`type_of_report` enum('Hazard','Concern/Suggestion')
,`reported_by` varchar(150)
,`status` enum('pending','resolved','open','in_progress','rejected')
,`incident_location` varchar(200)
,`inspected_by` varchar(150)
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `vw_incidents_per_month`
-- (See below for the actual view)
--
CREATE TABLE `vw_incidents_per_month` (
`year` int(4)
,`month` int(2)
,`month_name` varchar(9)
,`total` bigint(21)
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `vw_incident_summary`
-- (See below for the actual view)
--
CREATE TABLE `vw_incident_summary` (
`classification` enum('Near Miss','First Aid','Minor','Major','Damage to Property')
,`total` bigint(21)
);

-- --------------------------------------------------------

--
-- Structure for view `vw_concern_overview`
--
DROP TABLE IF EXISTS `vw_concern_overview`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_concern_overview`  AS SELECT sum(case when `concern_reports`.`report_type` = 'Hazard' then 1 else 0 end) AS `hazard_count`, sum(case when `concern_reports`.`report_type` = 'Concern/Suggestion' then 1 else 0 end) AS `suggestion_count` FROM `concern_reports` ;

-- --------------------------------------------------------

--
-- Structure for view `vw_dashboard_stats`
--
DROP TABLE IF EXISTS `vw_dashboard_stats`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_dashboard_stats`  AS SELECT (select count(0) from `incidents`) AS `total_incidents`, (select count(0) from `concern_reports` where `concern_reports`.`report_type` = 'Hazard') AS `hazards_identified`, (select count(0) from `incidents` where `incidents`.`status` = 'Resolved') AS `resolved_incidents`, (select count(0) from `incidents` where `incidents`.`status` in ('Open','Under Investigation')) AS `pending_incidents` ;

-- --------------------------------------------------------

--
-- Structure for view `vw_fire_inspection_counts`
--
DROP TABLE IF EXISTS `vw_fire_inspection_counts`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_fire_inspection_counts`  AS SELECT (select count(0) from `fire_inspection_extinguisher`) AS `extinguisher_count`, (select count(0) from `fire_inspection_light`) AS `light_count`, (select count(0) from `fire_inspection_hose`) AS `hose_count` ;

-- --------------------------------------------------------

--
-- Structure for view `vw_hazard_concern_list`
--
DROP TABLE IF EXISTS `vw_hazard_concern_list`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_hazard_concern_list`  AS SELECT `concern_reports`.`id` AS `id`, `concern_reports`.`report_date` AS `date`, `concern_reports`.`report_time` AS `time`, `concern_reports`.`report_type` AS `type_of_report`, `concern_reports`.`reported_by` AS `reported_by`, `concern_reports`.`status` AS `status`, `concern_reports`.`incident_location` AS `incident_location`, `concern_reports`.`inspected_by` AS `inspected_by` FROM `concern_reports` ORDER BY `concern_reports`.`report_date` DESC, `concern_reports`.`report_time` DESC ;

-- --------------------------------------------------------

--
-- Structure for view `vw_incidents_per_month`
--
DROP TABLE IF EXISTS `vw_incidents_per_month`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_incidents_per_month`  AS SELECT year(`incidents`.`incident_date`) AS `year`, month(`incidents`.`incident_date`) AS `month`, monthname(`incidents`.`incident_date`) AS `month_name`, count(0) AS `total` FROM `incidents` GROUP BY year(`incidents`.`incident_date`), month(`incidents`.`incident_date`) ORDER BY year(`incidents`.`incident_date`) ASC, month(`incidents`.`incident_date`) ASC ;

-- --------------------------------------------------------

--
-- Structure for view `vw_incident_summary`
--
DROP TABLE IF EXISTS `vw_incident_summary`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_incident_summary`  AS SELECT `incidents`.`classification` AS `classification`, count(0) AS `total` FROM `incidents` GROUP BY `incidents`.`classification` ;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admin_users`
--
ALTER TABLE `admin_users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indexes for table `certificates`
--
ALTER TABLE `certificates`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_cert_admin` (`uploaded_by`);

--
-- Indexes for table `cert_files`
--
ALTER TABLE `cert_files`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_folder_id` (`folder_id`);

--
-- Indexes for table `cert_folders`
--
ALTER TABLE `cert_folders`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `concern_reports`
--
ALTER TABLE `concern_reports`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_concern_type` (`report_type`),
  ADD KEY `idx_concern_status` (`status`),
  ADD KEY `idx_concern_date` (`report_date`);

--
-- Indexes for table `emergency_lights`
--
ALTER TABLE `emergency_lights`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_el_user` (`created_by_user_id`);

--
-- Indexes for table `employee_accounts`
--
ALTER TABLE `employee_accounts`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `employee_id` (`employee_id`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `idx_emp_role` (`role`);

--
-- Indexes for table `fire_equipment`
--
ALTER TABLE `fire_equipment`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_fire_type` (`equipment_type`);

--
-- Indexes for table `fire_extinguishers`
--
ALTER TABLE `fire_extinguishers`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_fe_user` (`created_by_user_id`);

--
-- Indexes for table `fire_hose_cabinets`
--
ALTER TABLE `fire_hose_cabinets`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_hose_user` (`created_by_user_id`);

--
-- Indexes for table `fire_inspection_extinguisher`
--
ALTER TABLE `fire_inspection_extinguisher`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_ext_date` (`date_inspected`),
  ADD KEY `fk_ext_equip` (`equipment_id`);

--
-- Indexes for table `fire_inspection_hose`
--
ALTER TABLE `fire_inspection_hose`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_hose_date` (`date_inspected`),
  ADD KEY `fk_hose_equip` (`equipment_id`);

--
-- Indexes for table `fire_inspection_light`
--
ALTER TABLE `fire_inspection_light`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_light_date` (`date_inspected`),
  ADD KEY `fk_light_equip` (`equipment_id`);

--
-- Indexes for table `fire_protection_inspections`
--
ALTER TABLE `fire_protection_inspections`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `hazard_reports`
--
ALTER TABLE `hazard_reports`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `incidents`
--
ALTER TABLE `incidents`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `control_no` (`control_no`),
  ADD KEY `idx_incident_date` (`incident_date`),
  ADD KEY `idx_incident_class` (`classification`),
  ADD KEY `fk_incident_emp` (`employee_id`),
  ADD KEY `fk_incident_admin` (`created_by`);

--
-- Indexes for table `investigation_body_parts`
--
ALTER TABLE `investigation_body_parts`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_report_part` (`report_id`,`body_part`);

--
-- Indexes for table `investigation_reports`
--
ALTER TABLE `investigation_reports`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_inv_incident` (`incident_id`);

--
-- Indexes for table `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `notification_alerts`
--
ALTER TABLE `notification_alerts`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_alert_date` (`alert_date`),
  ADD KEY `idx_alert_severity` (`severity`),
  ADD KEY `fk_alert_incident` (`related_incident_id`),
  ADD KEY `fk_alert_concern` (`related_concern_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_users_email` (`email`),
  ADD KEY `idx_users_active_name` (`is_active`,`full_name`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admin_users`
--
ALTER TABLE `admin_users`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `certificates`
--
ALTER TABLE `certificates`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `cert_files`
--
ALTER TABLE `cert_files`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `cert_folders`
--
ALTER TABLE `cert_folders`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `concern_reports`
--
ALTER TABLE `concern_reports`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `emergency_lights`
--
ALTER TABLE `emergency_lights`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `employee_accounts`
--
ALTER TABLE `employee_accounts`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `fire_equipment`
--
ALTER TABLE `fire_equipment`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `fire_extinguishers`
--
ALTER TABLE `fire_extinguishers`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `fire_hose_cabinets`
--
ALTER TABLE `fire_hose_cabinets`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `fire_inspection_extinguisher`
--
ALTER TABLE `fire_inspection_extinguisher`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `fire_inspection_hose`
--
ALTER TABLE `fire_inspection_hose`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `fire_inspection_light`
--
ALTER TABLE `fire_inspection_light`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `fire_protection_inspections`
--
ALTER TABLE `fire_protection_inspections`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `hazard_reports`
--
ALTER TABLE `hazard_reports`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `incidents`
--
ALTER TABLE `incidents`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `investigation_body_parts`
--
ALTER TABLE `investigation_body_parts`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `investigation_reports`
--
ALTER TABLE `investigation_reports`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `notifications`
--
ALTER TABLE `notifications`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `notification_alerts`
--
ALTER TABLE `notification_alerts`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `certificates`
--
ALTER TABLE `certificates`
  ADD CONSTRAINT `fk_cert_admin` FOREIGN KEY (`uploaded_by`) REFERENCES `admin_users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `cert_files`
--
ALTER TABLE `cert_files`
  ADD CONSTRAINT `cert_files_ibfk_1` FOREIGN KEY (`folder_id`) REFERENCES `cert_folders` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `emergency_lights`
--
ALTER TABLE `emergency_lights`
  ADD CONSTRAINT `fk_el_user` FOREIGN KEY (`created_by_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `fire_extinguishers`
--
ALTER TABLE `fire_extinguishers`
  ADD CONSTRAINT `fk_fe_user` FOREIGN KEY (`created_by_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `fire_hose_cabinets`
--
ALTER TABLE `fire_hose_cabinets`
  ADD CONSTRAINT `fk_hose_user` FOREIGN KEY (`created_by_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `fire_inspection_extinguisher`
--
ALTER TABLE `fire_inspection_extinguisher`
  ADD CONSTRAINT `fk_ext_equip` FOREIGN KEY (`equipment_id`) REFERENCES `fire_equipment` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `fire_inspection_hose`
--
ALTER TABLE `fire_inspection_hose`
  ADD CONSTRAINT `fk_hose_equip` FOREIGN KEY (`equipment_id`) REFERENCES `fire_equipment` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `fire_inspection_light`
--
ALTER TABLE `fire_inspection_light`
  ADD CONSTRAINT `fk_light_equip` FOREIGN KEY (`equipment_id`) REFERENCES `fire_equipment` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `incidents`
--
ALTER TABLE `incidents`
  ADD CONSTRAINT `fk_incident_admin` FOREIGN KEY (`created_by`) REFERENCES `admin_users` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_incident_emp` FOREIGN KEY (`employee_id`) REFERENCES `employee_accounts` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `investigation_body_parts`
--
ALTER TABLE `investigation_body_parts`
  ADD CONSTRAINT `fk_body_report` FOREIGN KEY (`report_id`) REFERENCES `investigation_reports` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `investigation_reports`
--
ALTER TABLE `investigation_reports`
  ADD CONSTRAINT `fk_inv_incident` FOREIGN KEY (`incident_id`) REFERENCES `incidents` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `notification_alerts`
--
ALTER TABLE `notification_alerts`
  ADD CONSTRAINT `fk_alert_concern` FOREIGN KEY (`related_concern_id`) REFERENCES `concern_reports` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_alert_incident` FOREIGN KEY (`related_incident_id`) REFERENCES `incidents` (`id`) ON DELETE SET NULL;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
