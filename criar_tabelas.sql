CREATE TABLE patient (
	patient_id		 BIGSERIAL NOT NULL,
	user_information_user_id BIGINT,
	PRIMARY KEY(user_information_user_id)
);

CREATE TABLE user_information (
	user_id	 BIGSERIAL,
	nome		 VARCHAR(200) NOT NULL,
	nacionalidade	 VARCHAR(120) NOT NULL,
	genero		 VARCHAR(120) NOT NULL,
	data_nascimento DATE NOT NULL,
	email		 VARCHAR(120) NOT NULL,
	telemovel	 VARCHAR(120) NOT NULL,
	username	 VARCHAR(120) NOT NULL,
	password	 VARCHAR(120) NOT NULL,
	PRIMARY KEY(user_id)
);

CREATE TABLE employee_contract (
	employee_id		 BIGSERIAL NOT NULL,
	contract_data_inicio	 DATE NOT NULL,
	contract_data_fim		 DATE NOT NULL,
	contract_salario		 FLOAT(8) NOT NULL,
	contract_detalhes_contrato VARCHAR(500) NOT NULL,
	user_information_user_id	 BIGINT,
	PRIMARY KEY(user_information_user_id)
);

CREATE TABLE assistant (
	assistant_id				 BIGSERIAL NOT NULL,
	employee_contract_user_information_user_id BIGINT,
	PRIMARY KEY(employee_contract_user_information_user_id)
);

CREATE TABLE nurse (
	nurse_id					 BIGSERIAL NOT NULL,
	hier_valor				 BIGINT NOT NULL,
	trabalho					 VARCHAR(250) NOT NULL,
	employee_contract_user_information_user_id BIGINT,
	PRIMARY KEY(employee_contract_user_information_user_id)
);

CREATE TABLE doctor (
	doctor_id					 BIGSERIAL NOT NULL,
	med_licenca				 VARCHAR(120) NOT NULL,
	employee_contract_user_information_user_id BIGINT,
	PRIMARY KEY(employee_contract_user_information_user_id)
);

CREATE TABLE hospitalization (
	hospitalization_id				 BIGSERIAL,
	data_entrada					 DATE NOT NULL,
	data_saida					 DATE NOT NULL,
	tipo						 VARCHAR(250) NOT NULL,
	quarto						 BIGINT NOT NULL,
	custo						 FLOAT(8) NOT NULL,
	bill_bill_id					 BIGINT NOT NULL,
	nurse_employee_contract_user_information_user_id BIGINT NOT NULL,
	patient_user_information_user_id		 BIGINT NOT NULL,
	PRIMARY KEY(hospitalization_id)
);

CREATE TABLE surgery (
	surgery_id					 BIGSERIAL,
	data_marcada					 DATE NOT NULL,
	hora_inicio					 NUMERIC(8,2) NOT NULL,
	hora_final					 NUMERIC(8,2) NOT NULL,
	sala_surgery					 BIGINT NOT NULL,
	tipo						 VARCHAR(250) NOT NULL,
	custo						 FLOAT(8) NOT NULL,
	hospitalization_hospitalization_id		 BIGINT,
	doctor_employee_contract_user_information_user_id BIGINT NOT NULL,
	PRIMARY KEY(surgery_id,hospitalization_hospitalization_id)
);

CREATE TABLE appointment (
	appointment_id					 BIGSERIAL,
	data_marcada					 DATE NOT NULL,
	hora_inicio					 NUMERIC(8,2) NOT NULL,
	hora_final					 NUMERIC(8,2) NOT NULL,
	tipo						 VARCHAR(250) NOT NULL,
	sala_appointment					 BIGINT NOT NULL,
	custo						 FLOAT(8) NOT NULL,
	bill_bill_id					 BIGINT NOT NULL,
	doctor_employee_contract_user_information_user_id BIGINT NOT NULL,
	patient_user_information_user_id			 BIGINT NOT NULL,
	PRIMARY KEY(appointment_id)
);

CREATE TABLE specialization (
	specialization_id BIGSERIAL,
	tipo		 VARCHAR(250) NOT NULL,
	PRIMARY KEY(specialization_id)
);

CREATE TABLE prescription (
	prescricao_id BIGSERIAL,
	data_inical	 DATE NOT NULL,
	data_final	 DATE NOT NULL,
	quantidade	 FLOAT(8) NOT NULL,
	PRIMARY KEY(prescricao_id)
);

CREATE TABLE medication_side_effect (
	medication_id		 BIGSERIAL,
	tipo			 VARCHAR(250) NOT NULL,
	side_effect_effects_id	 BIGSERIAL NOT NULL,
	side_effect_sintomas	 VARCHAR(250) NOT NULL,
	side_effect_probabiilidade INTEGER NOT NULL,
	PRIMARY KEY(medication_id)
);

CREATE TABLE bill (
	bill_id	 BIGSERIAL,
	custo_total FLOAT(8) NOT NULL,
	PRIMARY KEY(bill_id)
);

CREATE TABLE payment (
	payment_id	 BIGSERIAL NOT NULL,
	quantidade	 FLOAT(8) NOT NULL,
	data_maxima	 DATE NOT NULL,
	forma_pagamento VARCHAR(250) NOT NULL,
	bill_bill_id	 BIGINT,
	PRIMARY KEY(payment_id,bill_bill_id)
);

CREATE TABLE nurse_surgery (
	nurse_employee_contract_user_information_user_id BIGINT,
	surgery_surgery_id				 BIGINT,
	surgery_hospitalization_hospitalization_id	 BIGINT,
	PRIMARY KEY(nurse_employee_contract_user_information_user_id,surgery_surgery_id,surgery_hospitalization_hospitalization_id)
);

CREATE TABLE hospitalization_assistant (
	hospitalization_hospitalization_id			 BIGINT,
	assistant_employee_contract_user_information_user_id BIGINT NOT NULL,
	PRIMARY KEY(hospitalization_hospitalization_id)
);

CREATE TABLE prescription_appointment (
	prescription_prescricao_id BIGINT,
	appointment_appointment_id BIGINT NOT NULL,
	PRIMARY KEY(prescription_prescricao_id)
);

CREATE TABLE prescription_hospitalization (
	prescription_prescricao_id	 BIGINT,
	hospitalization_hospitalization_id BIGINT NOT NULL,
	PRIMARY KEY(prescription_prescricao_id)
);

CREATE TABLE medication_side_effect_prescription (
	medication_side_effect_medication_id BIGINT,
	prescription_prescricao_id		 BIGINT,
	PRIMARY KEY(medication_side_effect_medication_id,prescription_prescricao_id)
);

CREATE TABLE doctor_specialization (
	doctor_employee_contract_user_information_user_id BIGINT NOT NULL,
	specialization_specialization_id			 BIGINT,
	PRIMARY KEY(specialization_specialization_id)
);

CREATE TABLE nurse_nurse (
	nurse_employee_contract_user_information_user_id	 BIGINT,
	nurse_employee_contract_user_information_user_id1 BIGINT NOT NULL,
	PRIMARY KEY(nurse_employee_contract_user_information_user_id)
);

ALTER TABLE patient ADD CONSTRAINT patient_fk1 FOREIGN KEY (user_information_user_id) REFERENCES user_information(user_id);
ALTER TABLE user_information ADD UNIQUE (email, telemovel, username);
ALTER TABLE employee_contract ADD CONSTRAINT employee_contract_fk1 FOREIGN KEY (user_information_user_id) REFERENCES user_information(user_id);
ALTER TABLE assistant ADD UNIQUE (assistant_id);
ALTER TABLE assistant ADD CONSTRAINT assistant_fk1 FOREIGN KEY (employee_contract_user_information_user_id) REFERENCES employee_contract(user_information_user_id);
ALTER TABLE nurse ADD UNIQUE (nurse_id);
ALTER TABLE nurse ADD CONSTRAINT nurse_fk1 FOREIGN KEY (employee_contract_user_information_user_id) REFERENCES employee_contract(user_information_user_id);
ALTER TABLE doctor ADD UNIQUE (doctor_id);
ALTER TABLE doctor ADD CONSTRAINT doctor_fk1 FOREIGN KEY (employee_contract_user_information_user_id) REFERENCES employee_contract(user_information_user_id);
ALTER TABLE hospitalization ADD CONSTRAINT hospitalization_fk1 FOREIGN KEY (bill_bill_id) REFERENCES bill(bill_id);
ALTER TABLE hospitalization ADD CONSTRAINT hospitalization_fk2 FOREIGN KEY (nurse_employee_contract_user_information_user_id) REFERENCES nurse(employee_contract_user_information_user_id);
ALTER TABLE hospitalization ADD CONSTRAINT hospitalization_fk3 FOREIGN KEY (patient_user_information_user_id) REFERENCES patient(user_information_user_id);
ALTER TABLE surgery ADD CONSTRAINT surgery_fk1 FOREIGN KEY (hospitalization_hospitalization_id) REFERENCES hospitalization(hospitalization_id);
ALTER TABLE surgery ADD CONSTRAINT surgery_fk2 FOREIGN KEY (doctor_employee_contract_user_information_user_id) REFERENCES doctor(employee_contract_user_information_user_id);
ALTER TABLE appointment ADD UNIQUE (sala_appointment);
ALTER TABLE appointment ADD CONSTRAINT appointment_fk1 FOREIGN KEY (bill_bill_id) REFERENCES bill(bill_id);
ALTER TABLE appointment ADD CONSTRAINT appointment_fk2 FOREIGN KEY (doctor_employee_contract_user_information_user_id) REFERENCES doctor(employee_contract_user_information_user_id);
ALTER TABLE appointment ADD CONSTRAINT appointment_fk3 FOREIGN KEY (patient_user_information_user_id) REFERENCES patient(user_information_user_id);
ALTER TABLE medication_side_effect ADD UNIQUE (side_effect_effects_id);
ALTER TABLE payment ADD CONSTRAINT payment_fk1 FOREIGN KEY (bill_bill_id) REFERENCES bill(bill_id);
ALTER TABLE nurse_surgery ADD CONSTRAINT nurse_surgery_fk1 FOREIGN KEY (nurse_employee_contract_user_information_user_id) REFERENCES nurse(employee_contract_user_information_user_id);
ALTER TABLE nurse_surgery ADD CONSTRAINT nurse_surgery_fk2 FOREIGN KEY (surgery_surgery_id, surgery_hospitalization_hospitalization_id) REFERENCES surgery(surgery_id, hospitalization_hospitalization_id);
ALTER TABLE hospitalization_assistant ADD CONSTRAINT hospitalization_assistant_fk1 FOREIGN KEY (hospitalization_hospitalization_id) REFERENCES hospitalization(hospitalization_id);
ALTER TABLE hospitalization_assistant ADD CONSTRAINT hospitalization_assistant_fk2 FOREIGN KEY (assistant_employee_contract_user_information_user_id) REFERENCES assistant(employee_contract_user_information_user_id);
ALTER TABLE prescription_appointment ADD CONSTRAINT prescription_appointment_fk1 FOREIGN KEY (prescription_prescricao_id) REFERENCES prescription(prescricao_id);
ALTER TABLE prescription_appointment ADD CONSTRAINT prescription_appointment_fk2 FOREIGN KEY (appointment_appointment_id) REFERENCES appointment(appointment_id);
ALTER TABLE prescription_hospitalization ADD CONSTRAINT prescription_hospitalization_fk1 FOREIGN KEY (prescription_prescricao_id) REFERENCES prescription(prescricao_id);
ALTER TABLE prescription_hospitalization ADD CONSTRAINT prescription_hospitalization_fk2 FOREIGN KEY (hospitalization_hospitalization_id) REFERENCES hospitalization(hospitalization_id);
ALTER TABLE medication_side_effect_prescription ADD CONSTRAINT medication_side_effect_prescription_fk1 FOREIGN KEY (medication_side_effect_medication_id) REFERENCES medication_side_effect(medication_id);
ALTER TABLE medication_side_effect_prescription ADD CONSTRAINT medication_side_effect_prescription_fk2 FOREIGN KEY (prescription_prescricao_id) REFERENCES prescription(prescricao_id);
ALTER TABLE doctor_specialization ADD CONSTRAINT doctor_specialization_fk1 FOREIGN KEY (doctor_employee_contract_user_information_user_id) REFERENCES doctor(employee_contract_user_information_user_id);
ALTER TABLE doctor_specialization ADD CONSTRAINT doctor_specialization_fk2 FOREIGN KEY (specialization_specialization_id) REFERENCES specialization(specialization_id);
ALTER TABLE nurse_nurse ADD CONSTRAINT nurse_nurse_fk1 FOREIGN KEY (nurse_employee_contract_user_information_user_id) REFERENCES nurse(employee_contract_user_information_user_id);
ALTER TABLE nurse_nurse ADD CONSTRAINT nurse_nurse_fk2 FOREIGN KEY (nurse_employee_contract_user_information_user_id1) REFERENCES nurse(employee_contract_user_information_user_id);
