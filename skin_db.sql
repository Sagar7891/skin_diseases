-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: May 24, 2025 at 12:08 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `skin_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `prescriptions`
--

CREATE TABLE `prescriptions` (
  `id` int(11) NOT NULL,
  `patient_id` int(20) DEFAULT NULL,
  `medicine` varchar(255) DEFAULT NULL,
  `dosage` varchar(255) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `prescriptions`
--

INSERT INTO `prescriptions` (`id`, `patient_id`, `medicine`, `dosage`, `notes`, `created_at`) VALUES
(1, 2, 'parasitic', '5.6', 'no need', '2025-05-23 13:34:42');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `number` varchar(20) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `role` enum('user','doctor') NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `dob` date DEFAULT NULL,
  `image_path` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `name`, `email`, `number`, `password`, `role`, `created_at`, `dob`, `image_path`) VALUES
(1, 'Ajaycode', 'ajaycode@gmail.com', '7373327552', 'scrypt:32768:8:1$TAYKAmfHkd7iHnem$09142766f68f9c37f17dc84facd9b925820d749523a60f294f45b85fb8e6696c10d4fcc199479a5705cabf20fc341144091992fbc20d87be02a394f9588a7fed', 'doctor', '2025-04-26 07:51:49', '2025-04-26', 'ChatGPT_Image_Apr_17_2025_11_15_56_AM.png'),
(2, 'user123', 'user@gmail.com', '9988776655', 'scrypt:32768:8:1$iE8dHUY8sSzraG00$a1295b8ce26269d20dacdf3eb6d4e7225e37dc13f4d72f4d42ed527816f1c91187bc7bd9b2a85f08bce515f241e2ca01a935ae287cfeddf4940bd4a4bb2d114f', 'user', '2025-04-26 07:52:30', '2025-04-26', 'iot.png'),
(3, 'test', 'test@gmail.com', '99887766', 'scrypt:32768:8:1$5hD5IktySz66iRca$97f30972879c58d9a4c237e284026ecf8f6b6a1364807160c538da05b4eec156a6dd79438374170f37b5f8e19a86535c73ef275f245f653994463d64ae6b43d9', 'user', '2025-05-19 09:32:13', '2025-05-19', 'Screenshot_1372.png'),
(4, 'oppo', 'oppo@gmail.com', '9988776655', 'scrypt:32768:8:1$pSD2DCPw8PnY3JXe$7b53804d4bda50cb63afc2c3013f9038961e7e95dda7811ce451bd6901fea179c89c94bd8fb16a2e6a55ef6d849288017b3d12288e0bfe1cdc264e0f0f7494ac', 'user', '2025-05-19 11:13:40', '2025-05-19', 'Screenshot_1359.png'),
(5, 'a', 'a@gmail.com', '9988776655', 'scrypt:32768:8:1$EpJQeI63JJRf9lo9$dc91e716021a3f0c08203544c8138f032136055ad07e60a7f9dfbc767e7cd90fdcd0babd70ad0f65e9ac687767ed82eea13c8ab6a7c0bf569179764c148d737e', 'user', '2025-05-23 11:45:40', '2025-05-23', 'data-mining-projects.jpeg');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `prescriptions`
--
ALTER TABLE `prescriptions`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `prescriptions`
--
ALTER TABLE `prescriptions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
