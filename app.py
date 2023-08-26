import tensorflow as tf
import csv

def parse_tfrecord(example_proto):
    feature_description = {
        'Task_id': tf.io.FixedLenFeature([], tf.int64,default_value=0),
        'Instruction_str': tf.io.FixedLenFeature([], tf.string, default_value='')

        # ... Add the rest of your features here
        # 'Ui_obj_str_seq': tf.io.FixedLenFeature([], tf.string),
        # 'Ui_obj_word_id_seq': tf.io.FixedLenFeature([], tf.int64),
        # ...
    }
    return tf.io.parse_single_example(example_proto, feature_description)

def tfrecord_to_csv(tfrecord_filename, csv_filename):
    with open(csv_filename, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        # Write the header to the CSV file
        writer.writerow(['Task_id', 'Instruction_str', 'Instruction_word_id_seq', 
                         'Instruction_rule_id', 'Ui_obj_str_seq', 'Ui_obj_word_id_seq',
                         'Ui_obj_type_id_seq', 'Ui_obj_clickable_seq', 'Ui_obj_cord_x_seq',
                         'Ui_obj_cord_y_seq', 'Ui_obj_v_distance', 'Ui_obj_h_distance',
                         'Ui_obj_dom_distance', 'Ui_obj_dom_location_seq', 'Verb_id_seq',
                         'Ui_target_id_seq', 'Input_str_position_seq', 'Obj_desc_position_seq'])
        
        # Iterate over the TFRecord file
        for raw_record in tf.data.TFRecordDataset(tfrecord_filename):
            parsed_record = parse_tfrecord(raw_record)
            # Convert the TF tensors into Python types
            task_id = parsed_record['Task_id'].numpy()
            instruction_str = parsed_record['Instruction_str'].numpy().decode('utf-8')
            # ... Add the rest of your features here
            
            # Write to CSV
            writer.writerow([task_id, instruction_str])  # Add the rest of your features here

if __name__ == '__main__':
    tfrecord_filename = 'pixel_help_4.tfrecord'
    csv_filename = 'output.csv'
    tfrecord_to_csv(tfrecord_filename, csv_filename)
