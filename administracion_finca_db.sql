-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 13-06-2026 a las 20:10:22
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `administracion_finca_db`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `animales`
--

CREATE TABLE `animales` (
  `id_animal` int(11) NOT NULL,
  `numero_identificacion` varchar(20) NOT NULL,
  `id_especie` int(11) NOT NULL,
  `sexo` char(1) DEFAULT 'F',
  `id_lote` int(11) DEFAULT NULL,
  `fecha_nacimiento` date DEFAULT NULL,
  `categoria_insai` varchar(30) DEFAULT 'Maute',
  `fecha_registro` timestamp NOT NULL DEFAULT current_timestamp(),
  `ultima_actualizacion` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `id_estado` int(11) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `catalogo_vacunas`
--

CREATE TABLE `catalogo_vacunas` (
  `id_vacuna` int(11) NOT NULL,
  `nombre_enfermedad` varchar(100) NOT NULL,
  `especie_destino` int(11) NOT NULL,
  `frecuencia_dias` int(11) NOT NULL,
  `dias_retiro` int(11) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `catalogo_vacunas`
--

INSERT INTO `catalogo_vacunas` (`id_vacuna`, `nombre_enfermedad`, `especie_destino`, `frecuencia_dias`, `dias_retiro`) VALUES
(1, 'Fiebre Aftosa (Obligatorio Ciclo Nacional)', 1, 180, 0),
(2, 'Rabia Paralítica Bovina', 1, 365, 0),
(3, 'Brucelosis Bovina (Exclusivo Hembras Jóvenes)', 1, 0, 21),
(4, 'Polivalente Clostridiales (Triple / 7 u 8 Vías)', 1, 365, 21),
(5, 'Carbón Bacteriológico (Antrax)', 1, 365, 21),
(6, 'Linfadenitis Caseosa (\"Granos\" o \"Secas\")', 3, 365, 25),
(7, 'Clostridiosis / Enterotoxemia (Riñón Pulposo)', 3, 180, 21),
(8, 'Ectima Contagioso (Boquera)', 3, 0, 0),
(9, 'Peste Porcina Clásica (PPC / Fiebre Porcina)', 2, 365, 25),
(10, 'Erisipela Porcina', 2, 180, 21),
(11, 'Triple Porcina (PLE: Parvovirus-Leptospira-Erisipela)', 2, 180, 21);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `especies`
--

CREATE TABLE `especies` (
  `id_especie` int(11) NOT NULL,
  `nombre` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `especies`
--

INSERT INTO `especies` (`id_especie`, `nombre`) VALUES
(1, 'Bovino'),
(2, 'Porcino'),
(3, 'Ovino');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `estados`
--

CREATE TABLE `estados` (
  `id_estado` int(11) NOT NULL,
  `descripcion` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `estados`
--

INSERT INTO `estados` (`id_estado`, `descripcion`) VALUES
(1, 'Activo'),
(2, 'Muerto'),
(3, 'Vendido');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `lotes`
--

CREATE TABLE `lotes` (
  `id_lote` int(11) NOT NULL,
  `nombre_lote` varchar(100) NOT NULL,
  `id_especie` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `lotes_biologicos`
--

CREATE TABLE `lotes_biologicos` (
  `id_lote_bio` int(11) NOT NULL,
  `id_vacuna` int(11) NOT NULL,
  `numero_lote_comercial` varchar(50) NOT NULL,
  `laboratorio` varchar(100) NOT NULL,
  `veterinario_responsable` varchar(150) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `registros_biometricos`
--

CREATE TABLE `registros_biometricos` (
  `id_registro` int(11) NOT NULL,
  `id_animal` int(11) NOT NULL,
  `peso_kg` decimal(10,2) NOT NULL,
  `consumo_alimento_diario` decimal(10,2) DEFAULT 0.00,
  `fecha_pesaje` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `registro_vacunacion`
--

CREATE TABLE `registro_vacunacion` (
  `id_registro` int(11) NOT NULL,
  `id_animal` int(11) NOT NULL,
  `id_lote_bio` int(11) NOT NULL,
  `fecha_aplicacion` date NOT NULL,
  `fecha_proxima_dosis` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `animales`
--
ALTER TABLE `animales`
  ADD PRIMARY KEY (`id_animal`),
  ADD UNIQUE KEY `numero_identificacion` (`numero_identificacion`),
  ADD KEY `id_especie` (`id_especie`),
  ADD KEY `id_lote` (`id_lote`),
  ADD KEY `id_estado` (`id_estado`);

--
-- Indices de la tabla `catalogo_vacunas`
--
ALTER TABLE `catalogo_vacunas`
  ADD PRIMARY KEY (`id_vacuna`),
  ADD KEY `especie_destino` (`especie_destino`);

--
-- Indices de la tabla `especies`
--
ALTER TABLE `especies`
  ADD PRIMARY KEY (`id_especie`);

--
-- Indices de la tabla `estados`
--
ALTER TABLE `estados`
  ADD PRIMARY KEY (`id_estado`);

--
-- Indices de la tabla `lotes`
--
ALTER TABLE `lotes`
  ADD PRIMARY KEY (`id_lote`),
  ADD KEY `id_especie` (`id_especie`);

--
-- Indices de la tabla `lotes_biologicos`
--
ALTER TABLE `lotes_biologicos`
  ADD PRIMARY KEY (`id_lote_bio`),
  ADD KEY `id_vacuna` (`id_vacuna`);

--
-- Indices de la tabla `registros_biometricos`
--
ALTER TABLE `registros_biometricos`
  ADD PRIMARY KEY (`id_registro`),
  ADD KEY `id_animal` (`id_animal`);

--
-- Indices de la tabla `registro_vacunacion`
--
ALTER TABLE `registro_vacunacion`
  ADD PRIMARY KEY (`id_registro`),
  ADD KEY `id_animal` (`id_animal`),
  ADD KEY `id_lote_bio` (`id_lote_bio`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `animales`
--
ALTER TABLE `animales`
  MODIFY `id_animal` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `catalogo_vacunas`
--
ALTER TABLE `catalogo_vacunas`
  MODIFY `id_vacuna` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT de la tabla `especies`
--
ALTER TABLE `especies`
  MODIFY `id_especie` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `estados`
--
ALTER TABLE `estados`
  MODIFY `id_estado` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `lotes`
--
ALTER TABLE `lotes`
  MODIFY `id_lote` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `lotes_biologicos`
--
ALTER TABLE `lotes_biologicos`
  MODIFY `id_lote_bio` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `registros_biometricos`
--
ALTER TABLE `registros_biometricos`
  MODIFY `id_registro` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `registro_vacunacion`
--
ALTER TABLE `registro_vacunacion`
  MODIFY `id_registro` int(11) NOT NULL AUTO_INCREMENT;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `animales`
--
ALTER TABLE `animales`
  ADD CONSTRAINT `animales_ibfk_1` FOREIGN KEY (`id_especie`) REFERENCES `especies` (`id_especie`),
  ADD CONSTRAINT `animales_ibfk_2` FOREIGN KEY (`id_lote`) REFERENCES `lotes` (`id_lote`) ON DELETE SET NULL,
  ADD CONSTRAINT `animales_ibfk_3` FOREIGN KEY (`id_estado`) REFERENCES `estados` (`id_estado`);

--
-- Filtros para la tabla `catalogo_vacunas`
--
ALTER TABLE `catalogo_vacunas`
  ADD CONSTRAINT `catalogo_vacunas_ibfk_1` FOREIGN KEY (`especie_destino`) REFERENCES `especies` (`id_especie`) ON DELETE CASCADE;

--
-- Filtros para la tabla `lotes`
--
ALTER TABLE `lotes`
  ADD CONSTRAINT `lotes_ibfk_1` FOREIGN KEY (`id_especie`) REFERENCES `especies` (`id_especie`) ON DELETE SET NULL;

--
-- Filtros para la tabla `lotes_biologicos`
--
ALTER TABLE `lotes_biologicos`
  ADD CONSTRAINT `lotes_biologicos_ibfk_1` FOREIGN KEY (`id_vacuna`) REFERENCES `catalogo_vacunas` (`id_vacuna`) ON DELETE CASCADE;

--
-- Filtros para la tabla `registros_biometricos`
--
ALTER TABLE `registros_biometricos`
  ADD CONSTRAINT `registros_biometricos_ibfk_1` FOREIGN KEY (`id_animal`) REFERENCES `animales` (`id_animal`) ON DELETE CASCADE;

--
-- Filtros para la tabla `registro_vacunacion`
--
ALTER TABLE `registro_vacunacion`
  ADD CONSTRAINT `registro_vacunacion_ibfk_1` FOREIGN KEY (`id_animal`) REFERENCES `animales` (`id_animal`) ON DELETE CASCADE,
  ADD CONSTRAINT `registro_vacunacion_ibfk_2` FOREIGN KEY (`id_lote_bio`) REFERENCES `lotes_biologicos` (`id_lote_bio`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
