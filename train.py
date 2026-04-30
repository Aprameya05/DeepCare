import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
import config
import utils

def build_transfer_model(architecture_name):
    """Builds a robust transfer learning classifier head over the chosen backbone."""
    print(f"\n[BUILD] Building {architecture_name}...")
    
    if architecture_name == 'ResNet152V2':
        base_model = tf.keras.applications.ResNet152V2(include_top=False, input_shape=(*config.TARGET_SIZE, 3), weights='imagenet')
    elif architecture_name == 'DenseNet121':
        base_model = tf.keras.applications.DenseNet121(include_top=False, input_shape=(*config.TARGET_SIZE, 3), weights='imagenet')
    elif architecture_name == 'EfficientNetB4':
        base_model = tf.keras.applications.EfficientNetB4(include_top=False, input_shape=(*config.TARGET_SIZE, 3), weights='imagenet')
    else:
        raise ValueError(f"Unknown architecture: {architecture_name}")

    # Freeze base model originally
    base_model.trainable = False

    # Create classification head
    inputs = tf.keras.Input(shape=(*config.TARGET_SIZE, 3))
    x = base_model(inputs, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dense(256, activation='relu')(x)
    x = tf.keras.layers.Dropout(0.4)(x)
    x = tf.keras.layers.BatchNormalization()(x)
    outputs = tf.keras.layers.Dense(len(config.CLASSES), activation='softmax')(x)

    model = tf.keras.Model(inputs, outputs)
    return model, base_model

def train_and_evaluate():
    # 1. Purge data leakage
    utils.clean_data_leakage()

    # 2. Data Augmentation & Loading
    # Train/Val Split from flow_from_directory requires identical seeds
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        validation_split=config.VALIDATION_SPLIT,
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        shear_range=0.1,
        zoom_range=0.1,
        horizontal_flip=True,
        fill_mode='nearest'
    )
    
    test_datagen = ImageDataGenerator(rescale=1./255)

    train_gen = train_datagen.flow_from_directory(
        config.TRAIN_DIR,
        target_size=config.TARGET_SIZE,
        batch_size=config.BATCH_SIZE,
        subset='training',
        class_mode='categorical',
        shuffle=True,
        seed=42
    )

    val_gen = train_datagen.flow_from_directory(
        config.TRAIN_DIR,
        target_size=config.TARGET_SIZE,
        batch_size=config.BATCH_SIZE,
        subset='validation',
        class_mode='categorical',
        shuffle=True,
        seed=42
    )

    test_gen = test_datagen.flow_from_directory(
        config.TEST_DIR,
        target_size=config.TARGET_SIZE,
        batch_size=config.BATCH_SIZE,
        class_mode='categorical',
        shuffle=False
    )

    architectures = ['ResNet152V2', 'DenseNet121', 'EfficientNetB4']
    best_acc = 0.0
    best_model = None
    best_arch_name = ""

    # Callbacks
    early_stop = EarlyStopping(monitor='val_accuracy', patience=5, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, verbose=1)

    for arch in architectures:
        model, base = build_transfer_model(arch)
        
        # Phase 1: Train Head Only
        print(f"[PHASE 1] Training top classification head for {arch}...")
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=config.LEARNING_RATE),
                      loss='categorical_crossentropy', metrics=['accuracy'])
        
        model.fit(train_gen, epochs=5, validation_data=val_gen, callbacks=[early_stop, reduce_lr])
        
        # Phase 2: Fine-Tuning deeper layers
        print(f"[PHASE 2] Fine-tuning top 30 layers for {arch}...")
        base.trainable = True
        # Freeze all layers except the last 30
        for layer in base.layers[:-30]:
            layer.trainable = False
            
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
                      loss='categorical_crossentropy', metrics=['accuracy'])
                      
        # Save temporary checkpoint per architecture
        arch_checkpoint = ModelCheckpoint(f"{config.WEIGHTS_DIR}/{arch}_best.weights.h5", 
                                          monitor='val_accuracy', save_best_only=True, save_weights_only=True)
        
        history = model.fit(train_gen, epochs=config.EPOCHS, validation_data=val_gen, 
                            callbacks=[early_stop, reduce_lr, arch_checkpoint])
                            
        # Check validation peak performance
        val_acc = max(history.history['val_accuracy'])
        print(f"-> {arch} Val Accuracy: {val_acc:.4f}")
        
        if val_acc > best_acc:
            best_acc = val_acc
            best_model = model
            best_arch_name = arch

    print(f"\n[SUMMARY] Best architecture is {best_arch_name} with Validation Accuracy: {best_acc:.4f}")
    
    # Save the absolute best weights and models
    best_model.save_weights(config.BEST_WEIGHTS_PATH)
    best_model.save(config.FINAL_MODEL_H5)
    best_model.export(config.SAVED_MODEL_DIR)
    
    print(f"[SAVED] Weights deposited at {config.BEST_WEIGHTS_PATH}")
    print(f"[SAVED] Keras Model dumped at {config.FINAL_MODEL_H5}")
    print(f"[SAVED] SavedModel directory generated at {config.SAVED_MODEL_DIR}")
    
    # Final Evaluate on test_gen
    test_loss, test_acc = best_model.evaluate(test_gen)
    print(f"[TEST EVALUATION] Final accuracy on pure Test Set: {test_acc:.4f}")

if __name__ == '__main__':
    train_and_evaluate()
